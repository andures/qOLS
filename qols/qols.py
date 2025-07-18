import os
import sys
import math
from qgis.PyQt.QtCore import QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction
from qgis.core import (QgsProject, QgsMessageLog, Qgis, QgsVectorLayer, 
                      QgsFeature, QgsGeometry, QgsPoint, QgsField, 
                      QgsPolygon, QgsLineString, QgsFillSymbol,
                      QgsVectorFileWriter, QgsCoordinateTransform,
                      QgsCoordinateReferenceSystem)

from .qols_dockwidget import QolsDockWidget

class QOLS:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr(u'&QOLS')
        self.first_start = True
        self.panel = None

    def tr(self, message):
        return QCoreApplication.translate('QOLS', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):
        print(f"QOLS: add_action called with callback: {callback}")
        print(f"QOLS: add_to_toolbar: {add_to_toolbar}")
        print(f"QOLS: add_to_menu: {add_to_menu}")
        
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        print(f"QOLS: Action created: {action}")
        
        try:
            action.triggered.connect(callback)
            print("QOLS: Action connected to callback")
        except Exception as e:
            print(f"QOLS: Error connecting callback: {e}")
            
        action.setEnabled(enabled_flag)
        
        if status_tip is not None:
            action.setStatusTip(status_tip)
        
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        
        if add_to_toolbar:
            try:
                self.iface.addToolBarIcon(action)
                print("QOLS: Action added to toolbar")
            except Exception as e:
                print(f"QOLS: Error adding to toolbar: {e}")
        
        if add_to_menu:
            try:
                self.iface.addPluginToMenu(self.menu, action)
                print("QOLS: Action added to menu")
            except Exception as e:
                print(f"QOLS: Error adding to menu: {e}")
        
        self.actions.append(action)
        print(f"QOLS: Total actions: {len(self.actions)}")
        return action

    def initGui(self):
        print("QOLS: initGui called")
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        print(f"QOLS: Icon path: {icon_path}")
        print(f"QOLS: Icon exists: {os.path.exists(icon_path)}")
        
        try:
            self.add_action(
                icon_path,
                text=self.tr(u'QOLS'),
                callback=self.show_panel,
                parent=self.iface.mainWindow())
            print("QOLS: Action added successfully")
            self.first_start = True
        except Exception as e:
            print(f"QOLS: Error in initGui: {e}")
            import traceback
            traceback.print_exc()

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        if self.panel:
            self.panel.close()
            self.panel = None

    def show_panel(self):
        """Toggle the QOLS dockwidget panel (show/hide)"""
        print("QOLS: show_panel called - BUTTON CLICKED!")
        
        try:
            # If panel exists and is visible, hide it
            if self.panel and self.panel.isVisible():
                print("QOLS: Hiding existing panel")
                self.panel.hide()
                self.iface.messageBar().pushMessage(
                    "QOLS", 
                    "Panel closed!", 
                    level=Qgis.Info,
                    duration=2
                )
                return
            
            # If panel doesn't exist, create it
            if not self.panel:
                print("QOLS: Creating new panel")
                self.panel = QolsDockWidget(self.iface)
                # Add panel to RIGHT SIDE instead of left
                self.iface.addDockWidget(Qt.RightDockWidgetArea, self.panel)
                self.panel.closingPlugin.connect(self.on_close_panel)
                self.panel.calculateClicked.connect(self.on_calculate)
                self.panel.closeClicked.connect(self.on_close_panel)
                print("QOLS: Panel created successfully")
            else:
                print("QOLS: Panel already exists, showing it")
            
            # Show and raise the panel
            self.panel.show()
            self.panel.raise_()
            print("QOLS: Panel shown and raised")
            
            # Show success message
            self.iface.messageBar().pushMessage(
                "QOLS", 
                "Panel opened!", 
                level=Qgis.Info,
                duration=2
            )
            
        except Exception as e:
            print(f"QOLS Error in show_panel: {e}")
            import traceback
            traceback.print_exc()
            self.iface.messageBar().pushMessage(
                "QOLS Error", 
                f"Error showing panel: {str(e)}", 
                level=Qgis.Critical
            )

    def on_close_panel(self):
        """Hide the panel when close is clicked"""
        if self.panel:
            self.panel.hide()
            # Don't set to None to keep the panel for reuse

    def on_calculate(self):
        """Execute the selected surface calculation script with parameters"""
        try:
            params = self.panel.get_parameters()
            if not params:
                self.iface.messageBar().pushMessage("QOLS", "Error getting parameters", level=Qgis.Critical)
                return
                
            surface_type = params.get('surface_type')
            specific_params = params.get('specific_params', {})
            
            print(f"QOLS: Executing {surface_type} with params: {specific_params}")
            
            if surface_type == 'Approach Surface':
                self.execute_approach_surface(params)
            elif surface_type == 'Conical':
                self.execute_conical_surface(params)
            elif surface_type == 'Inner Horizontal':
                self.execute_inner_horizontal_surface(params)
            elif surface_type == 'OFZ':
                self.execute_ofz_surface(params)
            elif surface_type == 'Outer Horizontal':
                self.execute_outer_horizontal_surface(params)
            elif surface_type == 'Take-off Surface':
                self.execute_takeoff_surface(params)
            elif surface_type == 'Transitional Surface':
                self.execute_transitional_surface(params)
            else:
                self.iface.messageBar().pushMessage("QOLS", "Please select a surface type", level=Qgis.Warning)
                return
            
            # Show success message
            self.iface.messageBar().pushMessage(
                "QOLS Success", 
                f"{surface_type} calculation completed successfully", 
                level=Qgis.Success
            )
                
        except Exception as e:
            print(f"QOLS: Error in on_calculate: {e}")
            import traceback
            traceback.print_exc()
            self.iface.messageBar().pushMessage("QOLS Error", f"Error calculating surface: {str(e)}", level=Qgis.Critical)

    def execute_approach_surface(self, params):
        """Execute the approach surface calculation script with parameters"""
        script_path = os.path.join(self.plugin_dir, 'scripts', 'approach-surface-UTM.py')
        self.execute_script(script_path, params)

    def execute_conical_surface(self, params):
        """Execute the conical surface calculation script with parameters"""
        script_path = os.path.join(self.plugin_dir, 'scripts', 'conical.py')
        self.execute_script(script_path, params)

    def execute_inner_horizontal_surface(self, params):
        """Execute the inner horizontal surface calculation script with parameters"""
        script_path = os.path.join(self.plugin_dir, 'scripts', 'inner-horizontal-racetrack.py')
        self.execute_script(script_path, params)

    def execute_ofz_surface(self, params):
        """Execute the OFZ surface calculation script with parameters"""
        script_path = os.path.join(self.plugin_dir, 'scripts', 'OFZ_UTM.py')
        self.execute_script(script_path, params)

    def execute_outer_horizontal_surface(self, params):
        """Execute the outer horizontal surface calculation script with parameters"""
        script_path = os.path.join(self.plugin_dir, 'scripts', 'outer-horizontal.py')
        self.execute_script(script_path, params)

    def execute_takeoff_surface(self, params):
        """Execute the takeoff surface calculation script with parameters"""
        script_path = os.path.join(self.plugin_dir, 'scripts', 'take-off-surface_UTM.py')
        self.execute_script(script_path, params)

    def execute_transitional_surface(self, params):
        """Execute the transitional surface calculation script with parameters"""
        script_path = os.path.join(self.plugin_dir, 'scripts', 'TransitionalSurface_UTM.py')
        self.execute_script(script_path, params)

    def execute_script(self, script_path, params=None):
        """Execute a script with dynamic parameters."""
        if params is None:
            params = {}
            
        try:
            # Read the script file
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            print(f"QOLS: Executing script: {script_path}")
            
            # Extract specific parameters and add them to the main params
            specific_params = params.get('specific_params', {})
            
            # Create execution namespace with parameters
            exec_namespace = {
                'iface': self.iface,
                'QgsProject': QgsProject,
                'QgsVectorLayer': QgsVectorLayer,
                'QgsFeature': QgsFeature,
                'QgsGeometry': QgsGeometry,
                'QgsPoint': QgsPoint,
                'QgsField': QgsField,
                'QgsPolygon': QgsPolygon,
                'QgsLineString': QgsLineString,
                'Qgis': Qgis,
                'QgsFillSymbol': QgsFillSymbol,
                'QgsVectorFileWriter': QgsVectorFileWriter,
                'QgsCoordinateTransform': QgsCoordinateTransform,
                'QgsCoordinateReferenceSystem': QgsCoordinateReferenceSystem,
                'QVariant': QVariant,
                'QColor': QColor,
                'os': os,
                'sys': sys,
                'math': math,
                **params,  # Add all parameters
                **specific_params  # Add specific parameters directly
            }
            
            # Execute the script
            exec(script_content, exec_namespace)
            
            print(f"QOLS: Script executed successfully: {script_path}")
            
        except Exception as e:
            print(f"QOLS: Error executing script {script_path}: {e}")
            import traceback
            traceback.print_exc()
            self.iface.messageBar().pushMessage("QOLS Error", f"Script execution error: {str(e)}", level=Qgis.Critical)
            raise
