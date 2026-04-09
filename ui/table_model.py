import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant


class DataFrameTableModel(QAbstractTableModel):
    def __init__(self, dataframe=None):
        super().__init__()
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()

    @property
    def dataframe(self):
        return self._dataframe

    def set_dataframe(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._dataframe.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        value = self._dataframe.iat[index.row(), index.column()]

        if role in (Qt.DisplayRole, Qt.EditRole):
            return "" if pd.isna(value) else str(value)

        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False

        self._dataframe.iat[index.row(), index.column()] = value
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            return str(self._dataframe.columns[section]) if section < len(self._dataframe.columns) else ""

        return str(section + 1)

    def update_cell(self, row, col, value):
        if row >= self.rowCount() or col >= self.columnCount():
            return

        self._dataframe.iat[row, col] = value
        index = self.index(row, col)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
