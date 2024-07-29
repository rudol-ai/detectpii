import itertools
from functools import cached_property

import pandas as pd
from attr import define
from sqlalchemy import Engine, create_engine, text, URL

from detectpii.model import Catalog, Column, Table


@define(kw_only=True)
class PostgresCatalog(Catalog):
    """A collection of tables in a Postgres database and schema."""

    user: str
    password: str
    host: str
    port: int
    database: str
    schema: str

    @cached_property
    def engine(self) -> Engine:
        return create_engine(self.url)

    def detect_tables(self) -> None:
        query = text(
            f"""
            SELECT
                table_schema,
                table_name,
                column_name
            FROM
                information_schema.columns
            WHERE 1=1 
                  AND table_schema = :schema
            ORDER BY table_name, column_name;
        """
        )

        pg_engine = self.engine

        with pg_engine.connect() as conn:
            rows = conn.execute(
                statement=query,
                parameters={"schema": self.schema},
            )

            for table_name, table_rows in itertools.groupby(
                iterable=rows,
                key=lambda row: row[1],
            ):
                table = Table(
                    name=table_name,
                    schema=self.schema,
                    columns=[Column(name=table_row[-1]) for table_row in table_rows],
                )

                self.tables.append(table)

    def sample(
        self,
        table: Table,
        percentage: int = 10,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        sql = f"""
            SELECT *
            FROM {table.name}
            TABLESAMPLE BERNOULLI(%(percentage)s)
        """

        with self.engine.connect() as conn:
            return pd.read_sql(
                sql=sql,
                con=conn,
                params={
                    "table_name": table.name,
                    "percentage": percentage,
                },
            )

    @property
    def url(self) -> URL:
        return URL(
            username=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            host=self.host,
            query={},
            drivername="postgresql+psycopg2",
        )
