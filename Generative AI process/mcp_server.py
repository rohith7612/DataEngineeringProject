from mcp.server.fastmcp import FastMCP
from agent import execute_query as execute_sql

mcp = FastMCP("CEO Analytics")


@mcp.tool()
def run_sql(query: str):
    """
    Execute PostgreSQL query and return results.
    """

    result = execute_sql(query)

    return result.to_dict(
        orient="records"
    )

@mcp.tool()
def get_region_sales():

    query = """
    SELECT *
    FROM gold_region_sales
    """

    result = execute_sql(query)

    return result.to_dict(
        orient="records"
    )


@mcp.tool()
def get_top_products():

    query = """
    SELECT *
    FROM gold_top_products
    """

    result = execute_sql(query)

    return result.to_dict(
        orient="records"
    )

if __name__ == "__main__":
    mcp.run()
