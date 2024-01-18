# -*- coding: utf-8 -*-

import os
from copy import deepcopy
from io import StringIO

from PySide6.QtUiTools import QUiLoader
from PySide6 import QtCore, QtWidgets
from electricalsim.extensions.extension_classes import ExtensionBase
import pandas as pd
import pandapower as pp
from pandapower.pypower.printpf import printpf
from pandapower.pypower.ppoption import ppoption


directory = os.path.dirname(__file__)
input_ui_path = os.path.join(directory, 'input.ui')


class Extension(ExtensionBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.set_separate_thread(True)
        self.set_extension_window(True)

        loader = QUiLoader()
        ui_file_ = QtCore.QFile(input_ui_path)
        ui_file_.open(QtCore.QIODeviceBase.OpenModeFlag.ReadOnly)
        self.input_dialog = loader.load(ui_file_)
        self.input_dialog.setWindowIcon(self.egs_icon())

        self.compute_opf = False
        self.data = None

        self.copy_net = None  # Deepcopy of the network just before OPF calculation

    def read_data(self):
        """
        Returns the DataFrame with data costs. Colums are:

        'name', 'element_type', 'element_id',
        'bus', 'cp1_eur_per_mw', 'cp0_eur',
        'cq1_eur_per_mvar', 'cq0_eur',
        'cp2_eur_per_mw2', 'cq2_eur_per_mvar2'
        """
        data = pd.DataFrame(columns=['name', 'element_type', 'element_id',
                                     'bus', 'cp1_eur_per_mw', 'cp0_eur',
                                     'cq1_eur_per_mvar', 'cq0_eur',
                                     'cp2_eur_per_mw2', 'cq2_eur_per_mvar2'])  # Empty DataFrame

        try:
            for _, row in self.net.poly_cost.iterrows():
                new_data_row = pd.Series(index=['name', 'element_type', 'element_id',
                                                'bus', 'cp1_eur_per_mw', 'cp0_eur',
                                                'cq1_eur_per_mvar', 'cq0_eur',
                                                'cp2_eur_per_mw2', 'cq2_eur_per_mvar2'])

                type_ = row['et']
                element_id = row['element']
                new_data_row['element_id'] = element_id
                new_data_row['element_type'] = type_
                new_data_row['cp0_eur'] = row['cp0_eur']
                new_data_row['cp1_eur_per_mw'] = row['cp1_eur_per_mw']
                new_data_row['cp2_eur_per_mw2'] = row['cp2_eur_per_mw2']
                new_data_row['cq0_eur'] = row['cq0_eur']
                new_data_row['cq1_eur_per_mvar'] = row['cq1_eur_per_mvar']
                new_data_row['cq2_eur_per_mvar2'] = row['cq2_eur_per_mvar2']
                new_data_row['name'] = self.net[type_].at[element_id, 'name']
                if type_=='dcline':
                    bus_id_from = self.net.dcline.at[element_id, 'bus_from']
                    bus_id_to = self.net.dcline.at[element_id, 'bus_to']

                    bus_name_from = self.net.bus.at[bus_id_from, 'name']
                    bus_name_to = self.net.bus.at[bus_id_to, 'name']

                    new_data_row['bus'] = f"{bus_id_from} - {bus_id_to} ({bus_name_from} - {bus_name_to})"
                else:
                    bus_id = self.net[type_].at[element_id, 'bus']
                    bus_name = self.net.bus.at[bus_id, 'name']
                    new_data_row['bus'] = f"{bus_id} ({bus_name})"

                data = pd.concat((data, new_data_row.to_frame().T), axis=0, ignore_index=True)

        except KeyError:
            data = pd.DataFrame(columns=['name', 'element_type', 'element_id',
                                         'bus', 'cp1_eur_per_mw', 'cp0_eur',
                                         'cq1_eur_per_mvar', 'cq0_eur',
                                         'cp2_eur_per_mw2', 'cq2_eur_per_mvar2'])  # Empty DataFrame

        return data

    def __call__(self):
        if self.compute_opf is False:
            return

        self.input_dialog.selector.currentTextChanged.disconnect()
        self.net.poly_cost = self.net.poly_cost.iloc[0:0]  # Removing old data...

        for index, row in self.data.iterrows():
            pp.create_poly_cost(self.net, element=row['element_id'], et=row['element_type'],
                                cp1_eur_per_mw=row['cp1_eur_per_mw'],
                                cp0_eur=row['cp0_eur'],
                                cq1_eur_per_mvar=row['cq1_eur_per_mvar'],
                                cq0_eur=row['cq0_eur'],
                                cp2_eur_per_mw2=row['cp2_eur_per_mw2'],
                                cq2_eur_per_mvar2=row['cq2_eur_per_mvar2'],
                                index=index, check=True)

        # Removing piecewise linear costs...
        self.net.pwl_cost = self.net.pwl_cost.iloc[0:0]

        # Solving the OPF...
        calculate_voltage_angles = self.input_dialog.calculate_voltage_angles.isChecked()
        switch_rx_ratio = self.input_dialog.switch_rx_ratio.value()
        delta = self.input_dialog.delta.value() * 1e-6
        init = self.input_dialog.init.currentText()
        trafo3w_losses = self.input_dialog.trafo3w_losses.currentText()
        consider_line_temperature = self.input_dialog.consider_line_temperature.isChecked()
        self.copy_net = deepcopy(self.net)

        # tmp = sys.stdout  # Capture old stdout with a temporary variable
        my_result = StringIO()
        # sys.stdout = my_result  # New stdout liked to the new StrigIO object

        try:
            if self.input_dialog.radio_acopf.isChecked():
                pp.runopp(self.copy_net, verbose=False,
                          calculate_voltage_angles=calculate_voltage_angles,
                          check_connectivity=True, suppress_warnings=True,
                          switch_rx_ratio=switch_rx_ratio, delta=delta, init=init,
                          numba=True, trafo3w_losses=trafo3w_losses,
                          consider_line_temperature=consider_line_temperature,
                          OPF_VIOLATION=self.input_dialog.OPF_VIOLATION.value()*1e-6,
                          PDIPM_COSTTOL=self.input_dialog.PDIPM_COSTTOL.value()*1e-6,
                          PDIPM_GRADTOL=self.input_dialog.PDIPM_GRADTOL.value()*1e-6,
                          PDIPM_COMPTOL=self.input_dialog.PDIPM_COMPTOL.value()*1e-6,
                          PDIPM_FEASTOL=self.input_dialog.PDIPM_FEASTOL.value()*1e-6,
                          PDIPM_MAX_IT=self.input_dialog.PDIPM_MAX_IT.value(),
                          SCPDIPM_RED_IT=self.input_dialog.SCPDIPM_RED_IT.value())
            else:
                pp.rundcopp(self.copy_net, verbose=False, check_connectivity=True,
                            suppress_warnings=True, switch_rx_ratio=switch_rx_ratio,
                            delta=delta, trafo3w_losses=trafo3w_losses)

        except pp.optimal_powerflow.OPFNotConverged:
            self.print('Solver did not converge!')
            return
        # sys.stdout = tmp  # Back to normal

        if not self.copy_net['OPF_converged']:
            # title = 'Not converged!'
            # text_content = 'Solver did not converge.'
            # QtWidgets.QMessageBox.critical(self.input_dialog, title, text_content)
            self.print('Solver did not converge!')
            return

        ac = self.copy_net["_options"]["ac"]
        if ac is True:
            result = self.copy_net['_ppc_opf']
            init = self.copy_net["_options"]["init"]
            ppopt = ppoption(VERBOSE=True, PF_DC=not ac, INIT=init)
            ppopt['OUT_ALL'] = 1

            try:
                printpf(baseMVA=result["baseMVA"], bus=result["bus"], gen=result["gen"],
                        branch=result["branch"], f=result["f"], success=result["success"],
                        et=result["et"], fd=my_result, ppopt=ppopt)

                self.print(my_result.getvalue())
            except IndexError:
                self.print('Solver did not converge!')
                return
        else:
            self.print(f'OPTIMIZED COST: {self.compute_cost()}')

        self.print('\n\nGENERATORS:')
        self.print(self.copy_net.res_gen.to_string())

        self.print('\n\nSTATIC GENERATORS:')
        self.print(self.copy_net.res_sgen.to_string())

        self.print('\n\nBUSES:')
        self.print(self.copy_net.res_bus.to_string())

        self.print('\n\nEXTERNAL GRIDS:')
        self.print(self.copy_net.res_ext_grid.to_string())

        self.print('\n\nLINES:')
        self.print(self.copy_net.res_line.to_string())

        self.print('\n\nDC LINES:')
        self.print(self.copy_net.res_dcline.to_string())

        self.print('\n\nSTORAGES:')
        self.print(self.copy_net.res_storage.to_string())

        self.print('\n\nTWO-WINDING TRANSFORMERS:')
        self.print(self.copy_net.res_trafo.to_string())

        self.print('\n\nTHREE-WINDING TRANSFORMERS:')
        self.print(self.copy_net.res_trafo3w.to_string())

        self.print('\n\nLOADS:')
        self.print(self.copy_net.res_load.to_string())
    
    def before_running(self):
        """
        Exceuted just before showing the extension dialog.
        """
        self.data = self.read_data()

        # Reading data...
        for row in self.net.gen.iterrows():
            id_ = row[0]
            cols = row[1][['name', 'bus']]
            if id_ in self.data['element_id'].values and cols['name'] in self.data['name'].values:
                continue
            cols['bus'] = f"{cols['bus']} ({self.net.bus.at[cols['bus'], 'name']})"
            cols['element_type'] = 'gen'
            cols['element_id'] = id_
            self.data = pd.concat((self.data, cols.to_frame().T), axis=0, ignore_index=True)

        for row in self.net.sgen.iterrows():
            id_ = row[0]
            cols = row[1][['name', 'bus']]
            if id_ in self.data['element_id'].values and cols['name'] in self.data['name'].values:
                continue
            cols['bus'] = f"{cols['bus']} ({self.net.bus.at[cols['bus'], 'name']})"
            cols['element_type'] = 'sgen'
            cols['element_id'] = id_
            self.data = pd.concat((self.data, cols.to_frame().T), axis=0, ignore_index=True)

        for row in self.net.ext_grid.iterrows():
            id_ = row[0]
            cols = row[1][['name', 'bus']]
            if id_ in self.data['element_id'].values and cols['name'] in self.data['name'].values:
                continue
            cols['bus'] = f"{cols['bus']} ({self.net.bus.at[cols['bus'], 'name']})"
            cols['element_type'] = 'ext_grid'
            cols['element_id'] = id_
            self.data = pd.concat((self.data, cols.to_frame().T), axis=0, ignore_index=True)

        for row in self.net.storage.iterrows():
            id_ = row[0]
            cols = row[1][['name', 'bus']]
            if id_ in self.data['element_id'].values and cols['name'] in self.data['name'].values:
                continue
            cols['bus'] = f"{cols['bus']} ({self.net.bus.at[cols['bus'], 'name']})"
            cols['element_type'] = 'storage'
            cols['element_id'] = id_
            self.data = pd.concat((self.data, cols.to_frame().T), axis=0, ignore_index=True)

        for row in self.net.load.iterrows():
            id_ = row[0]
            cols = row[1][['name', 'bus']]
            if id_ in self.data['element_id'].values and cols['name'] in self.data['name'].values:
                continue
            cols['bus'] = f"{cols['bus']} ({self.net.bus.at[cols['bus'], 'name']})"
            cols['element_type'] = 'load'
            cols['element_id'] = id_
            self.data = pd.concat((self.data, cols.to_frame().T), axis=0, ignore_index=True)

        for row in self.net.dcline.iterrows():
            id_ = row[0]
            cols = pd.Series(index=['name', 'bus', 'element_type', 'element_id'])
            cols['name'] = row[1]['name']
            if id_ in self.data['element_id'].values and cols['name'] in self.data['name'].values:
                continue
            cols['bus'] = str(row[1]['from_bus']) + ' - ' + str(row[1]['to_bus']) +\
                f" ({self.net.bus.at[row[1]['from_bus'], 'name']} - {self.net.bus.at[row[1]['to_bus'], 'name']})"
            cols['element_type'] = 'dcline'
            cols['element_id'] = id_
            self.data = pd.concat((self.data, cols.to_frame().T), axis=0, ignore_index=True)

        self.data = self.data.fillna(0.0)  # Replace NaN with zeros
        names = list(self.data['name'])
        if not names:
            title = 'No enough data'
            text_content = 'There are no generators, external grids, storage devices,' \
                           ' DC lines or loads in this network.'
            QtWidgets.QMessageBox.critical(self.standard_extension_win.w, title, text_content)
            return

        # Selector (combobox)...
        self.input_dialog.selector.clear()
        self.input_dialog.selector.currentTextChanged.connect(self.change_selection)
        self.input_dialog.selector.addItems(names)

        # Real power coeffs...
        self.input_dialog.cp2_eur_per_mw2.valueChanged.connect(self.change_coeff)
        self.input_dialog.cp1_eur_per_mw.valueChanged.connect(self.change_coeff)
        self.input_dialog.cp0_eur.valueChanged.connect(self.change_coeff)

        # Reactive power coeffs...
        self.input_dialog.cq2_eur_per_mvar2.valueChanged.connect(self.change_coeff)
        self.input_dialog.cq1_eur_per_mvar.valueChanged.connect(self.change_coeff)
        self.input_dialog.cq0_eur.valueChanged.connect(self.change_coeff)

        # Showing the dialog...
        if self.input_dialog.exec():
            self.clear_output()
            self.compute_opf = True

    def change_coeff(self, *args):
        """
        Updates the parameters data when they are changed in the GUI.
        """
        name = self.input_dialog.selector.currentText()
        row = self.data[self.data['name']==name]

        # Modifying row...
        row['cp2_eur_per_mw2'] = self.input_dialog.cp2_eur_per_mw2.value()
        row['cp1_eur_per_mw'] = self.input_dialog.cp1_eur_per_mw.value()
        row['cp0_eur'] = self.input_dialog.cp0_eur.value()
        row['cq2_eur_per_mvar2'] = self.input_dialog.cq2_eur_per_mvar2.value()
        row['cq1_eur_per_mvar'] = self.input_dialog.cq1_eur_per_mvar.value()
        row['cq0_eur'] = self.input_dialog.cq0_eur.value()

        self.data[self.data['name']==name] = row

    def compute_cost(self):
        """
        Returns the total cost.
        """
        cost = 0.
        for _, row in self.data.iterrows():
            id_ = row['element_id']
            et = row['element_type']
            if et=='dcline':
                p_mw = self.copy_net.res_dcline.at[id_, 'p_from_mw']
                q_mvar = self.copy_net.res_dcline.at[id_, 'q_from_mvar']
            else:
                p_mw = self.copy_net[f'res_{et}'].at[id_, 'p_mw']
                q_mvar = self.copy_net[f'res_{et}'].at[id_, 'q_mvar']

            cost_p = (row['cp2_eur_per_mw2'] * p_mw**2 + row['cp1_eur_per_mw'] * p_mw +
                      row['cp0_eur'])

            cost_q = (row['cq2_eur_per_mvar2'] * q_mvar**2 + row['cq1_eur_per_mvar'] * q_mvar +
                      row['cq0_eur'])

            cost += cost_p + cost_q

        return cost

    def change_selection(self, name):
        """
        Shows a specific element data when its name is selected in the combobox.

        :param name: Element name
        :return: None
        """
        row = self.data.loc[self.data['name'] == name]

        idx = row.index[0]
        self.input_dialog.element_type.setText(row.at[idx, 'element_type'])
        self.input_dialog.element_id.setText(str(int(row.at[idx, 'element_id'])))
        self.input_dialog.bus.setText(str(row.at[idx, 'bus']))

        self.input_dialog.cp2_eur_per_mw2.setValue(row.at[idx, 'cp2_eur_per_mw2'])
        self.input_dialog.cp1_eur_per_mw.setValue(row.at[idx, 'cp1_eur_per_mw'])
        self.input_dialog.cp0_eur.setValue(row.at[idx, 'cp0_eur'])

        self.input_dialog.cq2_eur_per_mvar2.setValue(row.at[idx, 'cq2_eur_per_mvar2'])
        self.input_dialog.cq1_eur_per_mvar.setValue(row.at[idx, 'cq1_eur_per_mvar'])
        self.input_dialog.cq0_eur.setValue(row.at[idx, 'cq0_eur'])
        
    def finish(self):
        """
        Executed just after the OPF calculation.
        """
        self.graph.session_change_warning()
