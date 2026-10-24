import typer
import requests
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="Extract geographic coordinates from OpenStreetMap to Excel.")
console = Console()

def fetch_osm_data(area_name: str):
    overpass_url = "http://overpass-api.de/api/interpreter"
    # کوئری برای استخراج محله‌ها و مناطق شهری
    overpass_query = f"""
    [out:json];
    area[name="{area_name}"]->.searchArea;
    (
      node["place"="suburb"](area.searchArea);
      node["place"="neighbourhood"](area.searchArea);
    );
    out center;
    """
    response = requests.post(overpass_url, data={'data': overpass_query})
    response.raise_for_status()
    return response.json()

@app.command()
def extract(
    city: str = typer.Argument(..., help="Name of the city (e.g., Tehran)"),
    output: str = typer.Option("output.xlsx", "--output", "-o", help="Output Excel file name (.xlsx)")
):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Fetching neighborhood data for {city} from OSM...", total=None)
        
        try:
            data = fetch_osm_data(city)
            elements = data.get("elements", [])
            
            if not elements:
                progress.stop()
                console.print(f"[yellow]No structural data found for {city}.[/yellow]")
                raise typer.Exit()
                
            progress.update(task, description="[cyan]Structuring data into Excel spreadsheet...")
            
            records = []
            for el in elements:
                name = el.get("tags", {}).get("name", "Unknown")
                lat = el.get("lat")
                lon = el.get("lon")
                if lat and lon:
                    records.append({"Neighborhood/Place": name, "Latitude": lat, "Longitude": lon})
                    
            df = pd.DataFrame(records)
            df.to_excel(output, index=False)
            
            progress.stop()
            console.print(f"[green]✅ Successfully exported {len(records)} locations to {output}[/green]")
            
        except Exception as e:
            progress.stop()
            console.print(f"[red]❌ Error connecting to Overpass API: {str(e)}[/red]")
            raise typer.Exit(1)

if __name__ == "__main__":
    app()