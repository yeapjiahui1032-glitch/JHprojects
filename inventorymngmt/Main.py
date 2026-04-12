import typer
from click import UsageError
from rich.console import Console
from rich.table import Table
from Repo import create_table
from Model import Product
from Repo import get_allproducts, add_product, reduce_product_quantity, increase_product_quantity, delete_product

console = Console()
app = typer.Typer(invoke_without_command=True)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())

@app.command(short_help="initialize the database")
def init():
     create_table()
     console.print("[bold green]Database initialized successfully![/bold green]")

@app.command(short_help="add a new product")
def add(name: str, sku: int, quantity: int, min_stock: int, category: str, location: str):
    typer.echo(f"Adding new product...")
    add_product(Product(name=name, sku=sku, quantity=quantity, min_stock=min_stock, category=category, location=location))
    display()

@app.command(short_help="reduce stock quantity")
def reduce_product(id: int, quantity: int):
    typer.echo(f"Reducing stock quantity...")
    reduce_product_quantity(id, quantity)
    display()


@app.command(short_help="increase stock quantity")
def increase_product(id: int, quantity: int):
    typer.echo(f"Increasing stock quantity...")
    increase_product_quantity(id, quantity)
    display()

@app.command(short_help="clear product")
def clear_product(id: int):
    typer.echo(f"Clearing product...")
    delete_product(id)
    display()

@app.command(short_help="show all Products")
def display():
    stocks = get_allproducts()
    console.print("[bold magenta]-=-=-=-=-=-Product Tracker Application-=-=-=-=-=-[/bold magenta]",":notebook_with_decorative_cover:") 

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("id", style="dim", width=6)
    table.add_column("Name", min_width=12)
    table.add_column("SKU", min_width=12, justify="center")
    table.add_column("Quantity", min_width=12, justify="center")
    table.add_column("Min Stock", min_width=12, justify="center")
    table.add_column("Category", min_width=12, justify="center")
    table.add_column("Location", min_width=12, justify="center")
    table.add_column("Created date", min_width=12, justify="center")
    table.add_column("Status", min_width=12, justify="center")

    for _, stock in enumerate(stocks):
        depleted = ":red_circle:" if int(stock.quantity) < 1 else ":green_circle:"
        table.add_row(str(stock.id), stock.name, stock.sku, str(stock.quantity), str(stock.min_stock), stock.category, stock.location, stock.created_at, depleted)
    console.print(table)


if __name__ == "__main__":
    try:
        app(standalone_mode=False)
    except UsageError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        typer.echo("Use --help to see available commands.")
