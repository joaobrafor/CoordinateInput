# -*- coding: utf-8 -*-
import os
import math
from qgis.PyQt.QtCore import Qt, QCoreApplication, QTranslator, QSettings, QLocale
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QMessageBox, QDesktopWidget, QAction, QPushButton, QLabel, QHBoxLayout, QInputDialog, QDialogButtonBox, QSpinBox, QRadioButton, QFormLayout, QComboBox
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsVectorFileWriter, QgsWkbTypes, QgsApplication

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'coordinate_input_dialog_base.ui'))

class CoordinateInputDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(CoordinateInputDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(self.tr("Coordinate Input"))
        self.browseButton.clicked.connect(self.select_output_file)
        self.browseButtonLine.clicked.connect(self.select_output_file_line)
        self.browseButtonPolygon.clicked.connect(self.select_output_file_polygon)
        self.addRowButton.clicked.connect(self.add_table_row)
        self.removeRowButton.clicked.connect(self.remove_table_rows)
        self.importButton.clicked.connect(self.import_from_txt)
        self.exportButton.clicked.connect(self.export_to_txt)
        self.processButton.clicked.connect(self.process_coordinates_point)
        self.processLineButton.clicked.connect(self.process_coordinates_line)
        self.processPolygonButton.clicked.connect(self.process_coordinates_polygon)
        self.importGeometryButton.clicked.connect(self.import_from_geometry)
        self.output_path = None
        self.output_path_line = None
        self.output_path_polygon = None
        self.max_x_decimals = 0
        self.max_y_decimals = 0
        self.set_default_output_path()
        self.adjust_table_columns()
        self.setup_info_button()
        self.center_window()
        self.moveUpButton.clicked.connect(self.move_rows_up)
        self.moveDownButton.clicked.connect(self.move_rows_down)
        self.coordinateTableWidget.setSelectionMode(self.coordinateTableWidget.ExtendedSelection)
        self.coordinateTableWidget.setSelectionBehavior(self.coordinateTableWidget.SelectRows)

    def tr(self, message):
        return QCoreApplication.translate('CoordinateInputDialog', message)

    def find_blank_row(self):
        for i in range(self.coordinateTableWidget.rowCount()):
            item = self.coordinateTableWidget.item(i, 1)
            if item is None or item.text().strip() == "":
                return i
        return -1

    def move_rows_up(self):
        selected_rows = sorted(set(index.row() for index in self.coordinateTableWidget.selectedIndexes()))
        if not selected_rows or selected_rows[0] == 0:
            return
        for row in selected_rows:
            if row > 0:
                for col in range(self.coordinateTableWidget.columnCount()):
                    item_above = self.coordinateTableWidget.takeItem(row - 1, col)
                    item_current = self.coordinateTableWidget.takeItem(row, col)
                    self.coordinateTableWidget.setItem(row - 1, col, item_current)
                    self.coordinateTableWidget.setItem(row, col, item_above)
        self.coordinateTableWidget.clearSelection()
        selectionModel = self.coordinateTableWidget.selectionModel()
        for row in selected_rows:
            selectionModel.select(self.coordinateTableWidget.model().index(row - 1, 0), selectionModel.Select | selectionModel.Rows)

    def move_rows_down(self):
        selected_rows = sorted(set(index.row() for index in self.coordinateTableWidget.selectedIndexes()), reverse=True)
        if not selected_rows or selected_rows[0] == self.coordinateTableWidget.rowCount() - 1:
            return
        for row in selected_rows:
            if row < self.coordinateTableWidget.rowCount() - 1:
                for col in range(self.coordinateTableWidget.columnCount()):
                    item_below = self.coordinateTableWidget.takeItem(row + 1, col)
                    item_current = self.coordinateTableWidget.takeItem(row, col)
                    self.coordinateTableWidget.setItem(row + 1, col, item_current)
                    self.coordinateTableWidget.setItem(row, col, item_below)
        self.coordinateTableWidget.clearSelection()
        selectionModel = self.coordinateTableWidget.selectionModel()
        for row in selected_rows:
            selectionModel.select(self.coordinateTableWidget.model().index(row + 1, 0), selectionModel.Select | selectionModel.Rows)

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def set_default_output_path(self):
        self.output_path = ''
        self.outputPathLineEdit.setText(self.tr("Temporary Point File"))
        self.output_path_line = ''
        self.outputPathLineEditLine.setText(self.tr("Temporary Line File"))
        self.output_path_polygon = ''
        self.outputPathLineEditPolygon.setText(self.tr("Temporary Polygon File"))

    def adjust_table_columns(self):
        header = self.coordinateTableWidget.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(6):
            header.setSectionResizeMode(i, header.Stretch)

    def add_table_row(self):
        selected_rows = sorted(set(index.row() for index in self.coordinateTableWidget.selectedIndexes()))
        if not selected_rows:
            new_row = self.coordinateTableWidget.rowCount()
        else:
            new_row = selected_rows[-1] + 1
        self.coordinateTableWidget.insertRow(new_row)

    def remove_table_rows(self):
        selected_rows = sorted(set(index.row() for index in self.coordinateTableWidget.selectedIndexes()), reverse=True)
        for row in selected_rows:
            self.coordinateTableWidget.removeRow(row)

    def select_output_file(self):
        self.output_path, _ = QFileDialog.getSaveFileName(self, self.tr("Select Output File"), "", self.tr("GeoPackages (*.gpkg);;Shapefiles (*.shp)"))
        if self.output_path:
            self.outputPathLineEdit.setText(self.output_path)

    def select_output_file_line(self):
        self.output_path_line, _ = QFileDialog.getSaveFileName(self, self.tr("Select Output File for Line"), "", self.tr("GeoPackages (*.gpkg);;Shapefiles (*.shp)"))
        if self.output_path_line:
            self.outputPathLineEditLine.setText(self.output_path_line)

    def select_output_file_polygon(self):
        self.output_path_polygon, _ = QFileDialog.getSaveFileName(self, self.tr("Select Output File for Polygon"), "", self.tr("GeoPackages (*.gpkg);;Shapefiles (*.shp)"))
        if self.output_path_polygon:
            self.outputPathLineEditPolygon.setText(self.output_path_polygon)

    def import_from_txt(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("Import Coordinates"), "", self.tr("Text Files (*.txt)"))
        if file_path:
            with open(file_path, 'r') as file:
                lines = file.readlines()
                self.coordinateTableWidget.setRowCount(len(lines))
                for i, line in enumerate(lines):
                    parts = line.strip().split(';')
                    for j, part in enumerate(parts):
                        item = QTableWidgetItem(part)
                        self.coordinateTableWidget.setItem(i, j, item)

    def export_to_txt(self):
        file_path, _ = QFileDialog.getSaveFileName(self, self.tr("Export Coordinates"), "", self.tr("Text Files (*.txt)"))
        if file_path:
            with open(file_path, 'w') as file:
                row_count = self.coordinateTableWidget.rowCount()
                column_count = self.coordinateTableWidget.columnCount()
                for row in range(row_count):
                    line = []
                    for col in range(column_count):
                        item = self.coordinateTableWidget.item(row, col)
                        if item and item.text().strip():
                            line.append(item.text())
                        else:
                            line.append('')
                    if any(line):
                        file.write(';'.join(line) + '\n')

    def process_coordinates_point(self):
        points = self.extract_points()
        if not points:
            return
        self.create_shapefile(points, QgsWkbTypes.PointGeometry, self.output_path)

    def process_coordinates_line(self):
        points_by_id = self.extract_points_by_id()
        if not points_by_id:
            return
        lines = []
        line_id = 1
        for feature_id, points in points_by_id.items():
            if len(points) < 2:
                self.show_message(self.tr("Feature ID {} has fewer than 2 points and cannot form a line.").format(feature_id))
                continue
            for i in range(len(points) - 1):
                segment = [QgsPointXY(points[i][0], points[i][1]), QgsPointXY(points[i+1][0], points[i+1][1])]
                p = points[i]
                x_fmt = round(p[0], self.max_x_decimals)
                y_fmt = round(p[1], self.max_y_decimals)
                attributes = [
                    line_id,
                    int(p[7]),
                    p[6],
                    x_fmt,
                    y_fmt,
                    self.format_dd_to_dms(p[2], is_latitude=False),
                    self.format_dd_to_dms(p[3], is_latitude=True),
                    p[2],
                    p[3],
                    p[4],
                    p[5]
                ]
                lines.append((segment, attributes))
                line_id += 1
            segment = [QgsPointXY(points[-1][0], points[-1][1]), QgsPointXY(points[0][0], points[0][1])]
            p = points[-1]
            x_fmt = round(p[0], self.max_x_decimals)
            y_fmt = round(p[1], self.max_y_decimals)
            attributes = [
                line_id,
                int(p[7]),
                p[6],
                x_fmt,
                y_fmt,
                self.format_dd_to_dms(p[2], is_latitude=False),
                self.format_dd_to_dms(p[3], is_latitude=True),
                p[2],
                p[3],
                p[4],
                p[5]
            ]
            lines.append((segment, attributes))
            line_id += 1
        if not lines:
            self.show_message(self.tr("No valid line was created."))
            return
        self.create_shapefile(lines, QgsWkbTypes.LineGeometry, self.output_path_line, line=True)

    def process_coordinates_polygon(self):
        points_by_id = self.extract_points_by_id()
        if not points_by_id:
            return
        polygons = []
        for feature_id, points in points_by_id.items():
            if len(points) < 3:
                self.show_message(self.tr("Feature ID {} has fewer than 3 points and cannot form a polygon.").format(feature_id))
                continue
            polygon_points = [QgsPointXY(point[0], point[1]) for point in points]
            polygon_points.append(polygon_points[0])
            polygons.append((int(feature_id), polygon_points))
        if not polygons:
            self.show_message(self.tr("No valid polygon was created."))
            return
        self.create_shapefile(polygons, QgsWkbTypes.PolygonGeometry, self.output_path_polygon)

    def detect_decimal_count(self, text):
        text = text.strip()
        dec_sep = '.' if '.' in text else (',' if ',' in text else None)
        if not dec_sep:
            return 0
        after_sep = text.split(dec_sep)[1]
        return len(after_sep)

    def extract_points(self):
        points = []
        row_count = self.coordinateTableWidget.rowCount()
        project_crs = QgsProject.instance().crs()
        reference_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        transform_to_reference = QgsCoordinateTransform(project_crs, reference_crs, QgsProject.instance())
        transform_to_project = QgsCoordinateTransform(reference_crs, project_crs, QgsProject.instance())
        for row in range(row_count):
            feature_id_item = self.coordinateTableWidget.item(row, 5)
            feature_id = feature_id_item.text().strip() if feature_id_item and feature_id_item.text().strip() else "1"
            vertice_item = self.coordinateTableWidget.item(row, 0)
            x_item = self.coordinateTableWidget.item(row, 1)
            y_item = self.coordinateTableWidget.item(row, 2)
            z_item = self.coordinateTableWidget.item(row, 3)
            boundary_item = self.coordinateTableWidget.item(row, 4)
            if x_item and y_item:
                x_raw = x_item.text().strip()
                y_raw = y_item.text().strip()
                x = x_raw.replace(',', '.')
                y = y_raw.replace(',', '.')
                z = z_item.text().strip().replace(',', '.') if z_item and z_item.text().strip() else None
                boundary = boundary_item.text().strip() if boundary_item else ""
                try:
                    if ':' in x or ':' in y:
                        x_dd = self.parse_dms_coordinate(x)
                        y_dd = self.parse_dms_coordinate(y)
                    else:
                        x_dd = float(x)
                        y_dd = float(y)
                        if 100000 < abs(x_dd) < 1000000 and 0 < abs(y_dd) < 10000000:
                            point_utm = QgsPointXY(x_dd, y_dd)
                            point_wgs84 = transform_to_reference.transform(point_utm)
                            x_dd = point_wgs84.x()
                            y_dd = point_wgs84.y()
                    if (x_dd < -180 or x_dd > 180) or (y_dd < -90 or y_dd > 90):
                        self.show_message(self.tr("Error reading coordinates in row {}.").format(row + 1))
                        self.show_info()
                        return []
                    point_reference = QgsPointXY(x_dd, y_dd)
                    point_project = transform_to_project.transform(point_reference)
                except Exception:
                    self.show_message(self.tr("Error reading coordinates in row {}.").format(row + 1))
                    self.show_info()
                    return []
                x_dec = self.detect_decimal_count(x_raw)
                y_dec = self.detect_decimal_count(y_raw)
                if x_dec > self.max_x_decimals:
                    self.max_x_decimals = x_dec
                if y_dec > self.max_y_decimals:
                    self.max_y_decimals = y_dec
                points.append((
                    point_project.x(),
                    point_project.y(),
                    point_reference.x(),
                    point_reference.y(),
                    float(z) if z else None,
                    boundary,
                    vertice_item.text() if vertice_item else "",
                    feature_id
                ))
        if not points:
            self.show_message(self.tr("No valid coordinates provided."))
            self.show_info()
        return points

    def extract_points_by_id(self):
        points_by_id = {}
        row_count = self.coordinateTableWidget.rowCount()
        project_crs = QgsProject.instance().crs()
        reference_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        transform_to_reference = QgsCoordinateTransform(project_crs, reference_crs, QgsProject.instance())
        transform_to_project = QgsCoordinateTransform(reference_crs, project_crs, QgsProject.instance())
        for row in range(row_count):
            feature_id_item = self.coordinateTableWidget.item(row, 5)
            feature_id = feature_id_item.text().strip() if feature_id_item and feature_id_item.text().strip() else "1"
            vertice_item = self.coordinateTableWidget.item(row, 0)
            x_item = self.coordinateTableWidget.item(row, 1)
            y_item = self.coordinateTableWidget.item(row, 2)
            z_item = self.coordinateTableWidget.item(row, 3)
            boundary_item = self.coordinateTableWidget.item(row, 4)
            if x_item and y_item:
                x_raw = x_item.text().strip()
                y_raw = y_item.text().strip()
                x = x_raw.replace(',', '.')
                y = y_raw.replace(',', '.')
                z = z_item.text().strip().replace(',', '.') if z_item and z_item.text().strip() else None
                boundary = boundary_item.text().strip() if boundary_item else ""
                try:
                    if ':' in x or ':' in y:
                        x_dd = self.parse_dms_coordinate(x)
                        y_dd = self.parse_dms_coordinate(y)
                    else:
                        x_dd = float(x)
                        y_dd = float(y)
                        if 100000 < abs(x_dd) < 1000000 and 0 < abs(y_dd) < 10000000:
                            point_utm = QgsPointXY(x_dd, y_dd)
                            point_wgs84 = transform_to_reference.transform(point_utm)
                            x_dd = point_wgs84.x()
                            y_dd = point_wgs84.y()
                    if (x_dd < -180 or x_dd > 180) or (y_dd < -90 or y_dd > 90):
                        self.show_message(self.tr("Error reading coordinates in row {}.").format(row + 1))
                        self.show_info()
                        return {}
                    point_reference = QgsPointXY(x_dd, y_dd)
                    point_project = transform_to_project.transform(point_reference)
                except Exception:
                    self.show_message(self.tr("Error reading coordinates in row {}.").format(row + 1))
                    self.show_info()
                    return {}
                x_dec = self.detect_decimal_count(x_raw)
                y_dec = self.detect_decimal_count(y_raw)
                if x_dec > self.max_x_decimals:
                    self.max_x_decimals = x_dec
                if y_dec > self.max_y_decimals:
                    self.max_y_decimals = y_dec
                if feature_id not in points_by_id:
                    points_by_id[feature_id] = []
                points_by_id[feature_id].append((
                    point_project.x(),
                    point_project.y(),
                    point_reference.x(),
                    point_reference.y(),
                    float(z) if z else None,
                    boundary,
                    vertice_item.text() if vertice_item else "",
                    feature_id
                ))
        if not points_by_id:
            self.show_message(self.tr("No valid coordinates provided."))
            self.show_info()
        return points_by_id

    def parse_dms_coordinate(self, coord):
        parts = coord.split(':')
        if len(parts) == 3:
            degrees, minutes, seconds = parts
            direction = None
        elif len(parts) == 4:
            degrees, minutes, seconds, direction = parts
        else:
            raise ValueError(self.tr("Invalid coordinate format"))
        dd = self.convert_dms_to_dd(float(degrees), float(minutes), float(seconds))
        if direction is not None and direction in ['W', 'S']:
            dd = -dd
        return dd

    def convert_dms_to_dd(self, d, m, s):
        dd = abs(d) + (m / 60.0) + (s / 3600.0)
        return dd if d >= 0 else -dd

    def format_dd_to_dms(self, dd, is_latitude=True):
        direction = 'N' if dd >= 0 and is_latitude else 'S' if is_latitude else 'E' if dd >= 0 else 'W'
        dd = abs(dd)
        degrees = int(dd)
        minutes = int((dd - degrees) * 60)
        seconds = (dd - degrees - minutes / 60) * 3600
        seconds = round(seconds, 3)
        if seconds >= 60:
            minutes += 1
            seconds -= 60
        if minutes >= 60:
            degrees += 1
            minutes -= 60
        return f"{degrees}°{minutes:02d}'{seconds:06.3f}\" {direction}".replace('.', ',')

    def create_shapefile(self, features, geometry_type, output_path, line=False):
        crs = QgsProject.instance().crs()
        if geometry_type == QgsWkbTypes.PolygonGeometry:
            layer_name = self.tr('Output Polygons')
            layer = QgsVectorLayer('MultiPolygon?crs={}'.format(crs.authid()), layer_name, 'memory')
            pr = layer.dataProvider()
            pr.addAttributes([QgsField(self.tr('Feature_ID'), 2)])
            layer.updateFields()
            for feature_id, polygon_points in features:
                feature = QgsFeature()
                geometry = QgsGeometry.fromMultiPolygonXY([[polygon_points]])
                if geometry.isEmpty() or not geometry.isGeosValid():
                    continue
                feature.setGeometry(geometry)
                feature.setAttributes([feature_id])
                pr.addFeature(feature)
            layer.updateExtents()
            if output_path and output_path.strip():
                if output_path.lower().endswith('.shp'):
                    driver_name = "ESRI Shapefile"
                elif output_path.lower().endswith('.gpkg'):
                    driver_name = "GPKG"
                else:
                    driver_name = "GPKG"
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = driver_name
                options.fileEncoding = 'UTF-8'
                options.layerName = layer_name
                error, error_message = QgsVectorFileWriter.writeAsVectorFormatV2(
                    layer,
                    output_path,
                    QgsProject.instance().transformContext(),
                    options
                )
                if error == QgsVectorFileWriter.NoError:
                    if driver_name == "GPKG":
                        uri = "{}|layername={}".format(output_path, layer_name)
                        saved_layer = QgsVectorLayer(uri, layer_name, "ogr")
                    else:
                        saved_layer = QgsVectorLayer(output_path, layer_name, "ogr")
                    if saved_layer.isValid():
                        QgsProject.instance().addMapLayer(saved_layer)
                        self.show_message(self.tr("The layer was successfully created."))
                    else:
                        QMessageBox.warning(self, self.tr("Error"), self.tr("Failed to load saved layer."))
                else:
                    QMessageBox.warning(self, self.tr("Error saving file"), error_message)
            else:
                QgsProject.instance().addMapLayer(layer)
                self.show_message(self.tr("The temporary layer was successfully created."))
            return
        if geometry_type == QgsWkbTypes.PointGeometry:
            layer_name = self.tr('Output Points')
            layer = QgsVectorLayer('MultiPoint?crs={}'.format(crs.authid()), layer_name, 'memory')
        elif geometry_type == QgsWkbTypes.LineGeometry:
            layer_name = self.tr('Output Lines')
            layer = QgsVectorLayer('MultiLineString?crs={}'.format(crs.authid()), layer_name, 'memory')
        else:
            raise ValueError(self.tr("Unsupported geometry type"))
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField(self.tr('ID'), 2),
            QgsField(self.tr('Feature_ID'), 2),
            QgsField(self.tr('Vertex'), 10),
            QgsField(self.tr('X_UTM_LON'), 6, 'double', 30, self.max_x_decimals),
            QgsField(self.tr('Y_UTM_LAT'), 6, 'double', 30, self.max_y_decimals),
            QgsField(self.tr('X_GEO_LON'), 10),
            QgsField(self.tr('Y_GEO_LAT'), 10),
            QgsField(self.tr('X_DGEO_LON'), 6),
            QgsField(self.tr('Y_DGEO_LAT'), 6),
            QgsField(self.tr('Z_ALT'), 6),
            QgsField(self.tr('Boundary'), 10)
        ])
        layer.updateFields()
        if geometry_type == QgsWkbTypes.PointGeometry:
            for i, (x_project, y_project, x_geo, y_geo, z, boundary, vertice, feature_id) in enumerate(features):
                feature = QgsFeature()
                point = QgsPointXY(x_project, y_project)
                feature.setGeometry(QgsGeometry.fromMultiPointXY([point]))
                x_fmt = round(x_project, self.max_x_decimals)
                y_fmt = round(y_project, self.max_y_decimals)
                feature.setAttributes([
                    i + 1,
                    int(feature_id),
                    vertice,
                    x_fmt,
                    y_fmt,
                    self.format_dd_to_dms(x_geo, is_latitude=False),
                    self.format_dd_to_dms(y_geo, is_latitude=True),
                    x_geo,
                    y_geo,
                    z,
                    boundary
                ])
                pr.addFeature(feature)
        elif geometry_type == QgsWkbTypes.LineGeometry and line:
            for (line_points, attributes) in features:
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromMultiPolylineXY([line_points]))
                feature.setFields(layer.fields())
                feature.setAttributes(attributes)
                pr.addFeature(feature)
        layer.updateExtents()
        if output_path and output_path.strip():
            if output_path.lower().endswith('.shp'):
                driver_name = "ESRI Shapefile"
            elif output_path.lower().endswith('.gpkg'):
                driver_name = "GPKG"
            else:
                driver_name = "GPKG"
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = driver_name
            options.fileEncoding = 'UTF-8'
            options.layerName = layer_name
            error, error_message = QgsVectorFileWriter.writeAsVectorFormatV2(
                layer,
                output_path,
                QgsProject.instance().transformContext(),
                options
            )
            if error == QgsVectorFileWriter.NoError:
                if driver_name == "GPKG":
                    uri = "{}|layername={}".format(output_path, layer_name)
                    saved_layer = QgsVectorLayer(uri, layer_name, "ogr")
                else:
                    saved_layer = QgsVectorLayer(output_path, layer_name, "ogr")
                if saved_layer.isValid():
                    QgsProject.instance().addMapLayer(saved_layer)
                    self.show_message(self.tr("The layer was successfully created."))
                else:
                    QMessageBox.warning(self, self.tr("Error"), self.tr("Failed to load saved layer."))
            else:
                QMessageBox.warning(self, self.tr("Error saving file"), error_message)
        else:
            QgsProject.instance().addMapLayer(layer)
            self.show_message(self.tr("The temporary layer was successfully created."))

    def import_from_geometry(self):
        from qgis.utils import iface
        selected_layers = iface.layerTreeView().selectedLayers()
        if not selected_layers:
            self.show_message(self.tr("No layer selected."))
            return
        layer = selected_layers[0]
        geom_type = layer.geometryType()
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Import Options"))
        form_layout = QFormLayout(dialog)
        spin_decimals = QSpinBox(dialog)
        spin_decimals.setRange(1, 20)
        spin_decimals.setValue(6)
        form_layout.addRow(self.tr("Number of decimal places:"), spin_decimals)
        if geom_type != QgsWkbTypes.PolygonGeometry:
            hbox = QHBoxLayout()
            radio_yes = QRadioButton(self.tr("Yes"), dialog)
            radio_no = QRadioButton(self.tr("No"), dialog)
            radio_yes.setChecked(True)
            hbox.addWidget(radio_yes)
            hbox.addWidget(radio_no)
            form_layout.addRow(self.tr("Is it the same geometry?"), hbox)
            id_field_combo = QComboBox(dialog)
            id_field_combo.addItem(self.tr("Auto generate"))
            for field in layer.fields():
                id_field_combo.addItem(field.name())
            id_field_combo.setEnabled(False)
            form_layout.addRow(self.tr("Select Feature ID:"), id_field_combo)
            def update_combo_state():
                id_field_combo.setEnabled(radio_no.isChecked())
            radio_yes.toggled.connect(update_combo_state)
            radio_no.toggled.connect(update_combo_state)
        else:
            radio_yes = None
            id_field_combo = None
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        form_layout.addRow(button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        if dialog.exec_() != QDialog.Accepted:
            return
        decimals = spin_decimals.value()
        if geom_type != QgsWkbTypes.PolygonGeometry:
            same_geometry = radio_yes.isChecked()
        else:
            same_geometry = False
        id_field = None
        if not same_geometry and id_field_combo is not None:
            selected_field = id_field_combo.currentText()
            if selected_field != self.tr("Auto generate"):
                id_field = selected_field
        selected_features = layer.selectedFeatures()
        if not selected_features:
            self.show_message(self.tr("No feature selected."))
            return
        if layer.dataProvider().name() == "memory" and "ID" in [f.name() for f in layer.fields()]:
            try:
                selected_features = sorted(selected_features, key=lambda f: int(f.attribute("ID")))
            except Exception:
                selected_features = sorted(selected_features, key=lambda f: f.attribute("ID"))
        project_crs = QgsProject.instance().crs()
        layer_crs = layer.crs()
        transform = QgsCoordinateTransform(layer_crs, project_crs, QgsProject.instance())
        feature_id_counter = 1
        for feature in selected_features:
            if same_geometry:
                feature_id = "1"
            else:
                if id_field is not None:
                    feature_id = str(feature.attribute(id_field))
                else:
                    feature_id = str(feature_id_counter)
            geometry = feature.geometry()
            if geometry.type() == QgsWkbTypes.PolygonGeometry:
                if geometry.isMultipart():
                    parts = geometry.asMultiPolygon()
                else:
                    parts = [geometry.asPolygon()]
                for part in parts:
                    line = part[0]
                    vertices = [transform.transform(vertex) for vertex in line[:-1]]
                    northernmost_vertex = max(vertices, key=lambda p: p.y())
                    index = vertices.index(northernmost_vertex)
                    ordered_vertices = vertices[index:] + vertices[:index]
                    if not self.is_clockwise(ordered_vertices):
                        ordered_vertices.reverse()
                    for vertex in ordered_vertices:
                        row_position = self.find_blank_row()
                        if row_position == -1:
                            row_position = self.coordinateTableWidget.rowCount()
                            self.coordinateTableWidget.insertRow(row_position)
                        self.coordinateTableWidget.setItem(row_position, 0, QTableWidgetItem(""))
                        self.coordinateTableWidget.setItem(row_position, 1, QTableWidgetItem(f"{vertex.x():.{decimals}f}".replace('.', ',')))
                        self.coordinateTableWidget.setItem(row_position, 2, QTableWidgetItem(f"{vertex.y():.{decimals}f}".replace('.', ',')))
                        self.coordinateTableWidget.setItem(row_position, 3, QTableWidgetItem(""))
                        self.coordinateTableWidget.setItem(row_position, 4, QTableWidgetItem(""))
                        self.coordinateTableWidget.setItem(row_position, 5, QTableWidgetItem(feature_id))
            elif geometry.type() == QgsWkbTypes.LineGeometry:
                if geometry.isMultipart():
                    parts = geometry.asMultiPolyline()
                else:
                    parts = [geometry.asPolyline()]
                for part in parts:
                    if len(part) > 0:
                        first_vertex = transform.transform(part[0])
                        row_position = self.find_blank_row()
                        if row_position == -1:
                            row_position = self.coordinateTableWidget.rowCount()
                            self.coordinateTableWidget.insertRow(row_position)
                        self.coordinateTableWidget.setItem(row_position, 0, QTableWidgetItem(""))
                        self.coordinateTableWidget.setItem(row_position, 1, QTableWidgetItem(f"{first_vertex.x():.{decimals}f}".replace('.', ',')))
                        self.coordinateTableWidget.setItem(row_position, 2, QTableWidgetItem(f"{first_vertex.y():.{decimals}f}".replace('.', ',')))
                        self.coordinateTableWidget.setItem(row_position, 3, QTableWidgetItem(""))
                        self.coordinateTableWidget.setItem(row_position, 4, QTableWidgetItem(""))
                        self.coordinateTableWidget.setItem(row_position, 5, QTableWidgetItem(feature_id))
            elif geometry.type() == QgsWkbTypes.PointGeometry:
                points = geometry.asMultiPoint() if geometry.isMultipart() else [geometry.asPoint()]
                for point in points:
                    transformed_point = transform.transform(point)
                    row_position = self.find_blank_row()
                    if row_position == -1:
                        row_position = self.coordinateTableWidget.rowCount()
                        self.coordinateTableWidget.insertRow(row_position)
                    self.coordinateTableWidget.setItem(row_position, 0, QTableWidgetItem(""))
                    self.coordinateTableWidget.setItem(row_position, 1, QTableWidgetItem(f"{transformed_point.x():.{decimals}f}".replace('.', ',')))
                    self.coordinateTableWidget.setItem(row_position, 2, QTableWidgetItem(f"{transformed_point.y():.{decimals}f}".replace('.', ',')))
                    self.coordinateTableWidget.setItem(row_position, 3, QTableWidgetItem(""))
                    self.coordinateTableWidget.setItem(row_position, 4, QTableWidgetItem(""))
                    self.coordinateTableWidget.setItem(row_position, 5, QTableWidgetItem(feature_id))
            if not same_geometry:
                feature_id_counter += 1

    def is_clockwise(self, points):
        sum_over_edges = 0
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            sum_over_edges += (p2.x() - p1.x()) * (p2.y() + p1.y())
        p1 = points[-1]
        p2 = points[0]
        sum_over_edges += (p2.x() - p1.x()) * (p2.y() + p1.y())
        return sum_over_edges >= 0

    def setup_info_button(self):
        info_icon_path = os.path.join(os.path.dirname(__file__), 'icon_info.png')
        self.info_label = QLabel(self.tr("Coordinate Input Information:"))
        self.info_button = QPushButton()
        self.info_button.setIcon(QIcon(info_icon_path))
        self.info_button.clicked.connect(self.show_info)
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.info_label)
        header_layout.addWidget(self.info_button)
        header_layout.addStretch()
        self.verticalLayout.insertLayout(3, header_layout)

    def show_message(self, message):
        QMessageBox.information(self, self.tr("Information"), message)

    def show_info(self):
        info_text = (
            self.tr("In this plugin, the coordinate fields accept values in the following formats: ")
            + self.tr("X / E (lon) and Y / N (lat) Fields: ")
            + self.tr("- Decimal Degrees: Use numbers with a decimal separator (e.g., 48.8566, -2.3522 or 48,8566, -2,3522 using commas). ")
            + self.tr("- Degrees-Minutes-Seconds (DMS): Use the format DD:MM:SS[D] (e.g., 48:51:23N, 2:21:08W); if no letter is provided, use a negative sign in the degrees (e.g., -2:21:08 to indicate West or South). ")
            + self.tr("- UTM Coordinates: Use numeric values (e.g., 500000, 5412000) if within the range 100000 < X < 1000000 and 0 < Y < 10000000; these will be transformed to WGS 84 (EPSG:4326). ")
            + self.tr("Z (alt) Field: Optional, accepts numeric values. ")
            + self.tr("Vertex and Boundary Fields: Optional, can be left blank. ")
            + self.tr("Feature ID: Optional field to group coordinates. ")
            + self.tr("Decimals: Both decimal and comma separators are accepted. ")
            + self.tr("Note: Ensure coordinates are valid and consistent with the project’s CRS or WGS 84.")
        )
        QMessageBox.information(self, self.tr("Information"), info_text)

class CoordinateInput:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr('&Coordinate Input')
        self.toolbar = self.iface.addToolBar('CoordinateInput')
        self.toolbar.setObjectName('CoordinateInput')
        self.dlg = None
        self.translator = QTranslator()
        s = QSettings()
        user_locale = s.value("locale/userLocale", QLocale.system().name())
        locale = user_locale.split('_')[0]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'coordinate_input_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator.load(locale_path)
            QgsApplication.instance().installTranslator(self.translator)
        else:
            fallback_locale_path = os.path.join(self.plugin_dir, 'i18n', 'coordinate_input_en.qm')
            if os.path.exists(fallback_locale_path):
                self.translator.load(fallback_locale_path)
                QgsApplication.instance().installTranslator(self.translator)

    def tr(self, message):
        return QCoreApplication.translate('CoordinateInputDialog', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):
        action = QAction(QIcon(icon_path), text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if status_tip:
            action.setStatusTip(status_tip)
        if whats_this:
            action.setWhatsThis(whats_this)
        if add_to_menu:
            self.iface.addPluginToVectorMenu(self.menu, action)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr('Coordinate Input'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )

    def unload(self):
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.tr('&Coordinate Input'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        self.dlg = CoordinateInputDialog()
        self.dlg.setWindowModality(Qt.NonModal)
        self.dlg.show()

def classFactory(iface):
    return CoordinateInput(iface)
