from pydantic import BaseModel


class RequestTable(BaseModel):
    table_name: str
    label_column_name: str
    data_column_name: str
