import typer
import httpx
import datetime
import os
import asyncio
from dateutil.relativedelta import relativedelta
from typing import Optional
from typing_extensions import Annotated
from rich import print
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from weather_app import __app_name__, __version__


# api key is set as an environment variable
API_KEY = os.getenv('WEATHER_API_KEY')
BASE_URL = 'http://api.weatherapi.com/v1'

degree: str = chr(176)

app = typer.Typer()
console = Console()


async def request_data(params_dict_list: list[dict], verbose: bool = False) -> list[dict]:
    tasks = []

    async with httpx.AsyncClient() as client:
        for params in params_dict_list:
            tasks.append(client.get('http://api.weatherapi.com/v1/forecast.json', params=params))

        response_list = await asyncio.gather(*tasks)

    data_list = []

    for response in response_list:
        response_content = response.json()
        status_code = response.status_code

        if not response.is_success:
            error_message = response_content['error']['message']

            if verbose:
                error_code = response_content['error']['code']
                print(f'[red][bold]ERROR {error_code} (status code {status_code}):[/bold] {error_message}[/red]')

            else:
                print(f'[red][bold]ERROR:[/bold] {error_message}[/red]')

            raise ValueError

        else:
            data_list.append(response.json())

    return data_list


def generate_summary_panel(response_dict: dict) -> Panel:
    """
    Generates a summary panel for a single time/location input.

    :param response_dict: the json dictionary from a single time/location api request.
    :return: a rich Panel object summarizing the data.
    """

    place: str = response_dict['location']['name']
    country: str = response_dict['location']['country']
    condition: str = response_dict['current']['condition']['text']
    temperature: float = response_dict['current']['temp_c']
    humidity: int = response_dict['current']['humidity']
    timestring: str = response_dict['current']['last_updated']

    panel_string = (f'[bold green]{place} ({country})[/bold green]'
                    f'\n[yellow]{condition}[/yellow]'
                    f'\nTemperature: [cyan]{temperature} {degree}C[/cyan]'
                    f'\nHumidity (%): [cyan]{humidity}[/cyan]'
                    f'\nTime: [cyan]{timestring}[/cyan]')

    return Panel(panel_string, expand=False)


def generate_hourly_table(response_dict: dict) -> Table:
    """
    Generates a summary table for the hourly forecast.

    :param response_dict: the json dictionary from an hourly forecast api request.
    :return: a rich Table object summarizing the hourly forecast.
    """
    datetime_now = datetime.datetime.now()

    place: str = response_dict['location']['name']
    country: str = response_dict['location']['country']
    date: str = response_dict['forecast']['forecastday'][0]['date']
    hourly_dict = response_dict['forecast']['forecastday'][0]['hour']

    table = Table(
        show_footer=False,
        title=f'[bold]Weather forecast for {place} ({country}) for {date}[/bold]',
        title_justify='left'
    )

    table.add_column('Time', style='cyan', justify='center')
    table.add_column('Condition', style='green', justify='center')
    table.add_column(f'Temperature ({degree}C)', style='yellow', justify='center')
    table.add_column('Humidity (%)', style='blue', justify='center')
    table.add_column('Chance of rain (%)', style='dark_cyan', justify='center')

    for entry in hourly_dict:
        datetime_hour = datetime.datetime.strptime(entry['time'], '%Y-%m-%d %H:%M')

        if datetime_hour >= datetime_now:
            table.add_row(
                entry['time'].split(' ')[1],
                entry['condition']['text'],
                str(entry['temp_c']),
                str(entry['humidity']),
                str(entry['chance_of_rain'])
            )

    return table


def generate_daily_table(response_list: list[dict]) -> Table:
    """
    Generates a summary table for the daily forecast.

    :param response_list: a list of individual responses from an api request.
    :return: a rich Table object summarizing the hourly forecast.
    """
    response_dict = response_list[0]

    place: str = response_dict['location']['name']
    country: str = response_dict['location']['country']

    table = Table(
        show_footer=False,
        title=f'[bold]Weather forecast for {place} ({country}) for the next {len(response_list)} days[/bold]',
        title_justify='left'
    )

    table.add_column('Time', style='cyan', justify='center')
    table.add_column('Condition', style='green', justify='center')
    table.add_column(f'Temperature min/max ({degree}C)', style='yellow', justify='center')
    table.add_column('Humidity (%)', style='blue', justify='center')
    table.add_column('Chance of rain (%)', style='dark_cyan', justify='center')
    table.add_column('Total precipitation (mm)', style='magenta', justify='center')
    table.add_column('Sunrise/sunset', style='red', justify='center')

    for response in response_list:
        date = response['forecast']['forecastday'][0]['date']
        condition = response['forecast']['forecastday'][0]['day']['condition']['text']
        min_temp = response['forecast']['forecastday'][0]['day']['mintemp_c']
        max_temp = response['forecast']['forecastday'][0]['day']['maxtemp_c']
        avg_humidity = response['forecast']['forecastday'][0]['day']['avghumidity']
        chance_of_rain = response['forecast']['forecastday'][0]['day']['daily_chance_of_rain']
        total_precip = response['forecast']['forecastday'][0]['day']['totalprecip_mm']
        sunrise = response['forecast']['forecastday'][0]['astro']['sunrise']
        sunset = response['forecast']['forecastday'][0]['astro']['sunset']

        table.add_row(
            date,
            condition,
            f'{min_temp} / {max_temp}',
            str(avg_humidity),
            str(chance_of_rain),
            str(total_precip),
            f'{sunrise} / {sunset}'
        )

    return table


def generate_search_table(response_dict: dict) -> Table:
    """
    Generates a summary table for a location search request.

    :param response_dict: the json dictionary from a location search api request.
    :return: a rich Table object summarizing the search results.
    """

    table = Table(
        show_footer=False,
        title='[bold]Search results[/bold]',
        title_justify='left'
    )

    table.add_column('Id', style='cyan', justify='center')
    table.add_column('Name', style='green', justify='center')
    table.add_column('Region', style='yellow', justify='center')
    table.add_column('Country', style='red', justify='center')
    table.add_column('Coordinates', style='blue', justify='center')

    for entry in response_dict:
        coord_string = f"{entry['lat']}, {entry['lon']}"

        table.add_row(
            str(entry['id']),
            entry['name'],
            entry['region'],
            entry['country'],
            coord_string
        )

    return table


@app.command()
def search(
        location: Annotated[str, typer.Argument(help='The location name')],
        verbose: Annotated[bool, typer.Option(help='Provides full error log')] = False
    ) -> None:
    """
    Search for a specific location based on an input string.

    :param location: the input string for search query.
    :param verbose: provides a more detailed log in case of error.
    :return:
    """

    console.log(f'Fetching data for location {location}...')

    url = BASE_URL + '/search.json'

    params = {'key': API_KEY, 'q': location}
    response = httpx.get(url, params=params)
    response_content = response.json()
    status_code = response.status_code

    if response.is_success:
        console.log('Request successful')

        if not response_content:
            console.log('The search returned no result')

        else:
            search_table = generate_search_table(response_content)
            console.print(search_table)

    else:
        error_message = response_content['error']['message']

        if verbose:
            error_code = response_content['error']['code']
            print(f'[red][bold]ERROR {error_code} (status code {status_code}):[/bold] {error_message}[/red]')

        else:
            print(f'[red][bold]ERROR:[/bold] {error_message}[/red]')


@app.command()
def current(
        location: Annotated[str, typer.Argument(help='The location name or "lat, lon" string')],
        verbose: Annotated[bool, typer.Option(help='Provides full error log')] = False
    ) -> None:
    """
    Get the current weather for the specified location (if found).

    :param location: the input string for search query.
    :param verbose: provides a more detailed log in case of error.
    :return:
    """

    console.log(f'Fetching data for location {location}...')

    url = BASE_URL + '/current.json'

    params = {'key': API_KEY, 'q': location}
    response = httpx.get(url, params=params)
    response_content = response.json()
    status_code = response.status_code

    if response.is_success:
        console.log('Request successful')
        summary_panel = generate_summary_panel(response_content)
        console.print(summary_panel)

    else:
        error_message = response_content['error']['message']

        if verbose:
            error_code = response_content['error']['code']
            print(f'[red][bold]ERROR {error_code} (status code {status_code}):[/bold] {error_message}[/red]')

        else:
            print(f'[red][bold]ERROR:[/bold] {error_message}[/red]')


@app.command()
def forecast(
        location: Annotated[str, typer.Argument(help='The location name or "lat, lon" string '
                                                     'or id:XXXXXXX from the search function')],
        date: Annotated[str, typer.Option(help='Date of the forecast in yyyy-mm-dd')] = None,
        days: Annotated[int, typer.Option(help='How many days to forecast (up to 14)')] = None,
        hourly: Annotated[bool, typer.Option(help="Provide hourly values for the forecast")] = False,
        verbose: Annotated[bool, typer.Option(help='Provides full error log')] = False
    ) -> None:
    """
    Generates a forecast based on the input parameters/flags.

    :param location: the input string for search query.
    :param date: any date up to 14 days in the future.
    :param days: days to be forecasted (up to 14).
    :param hourly: bool parameter to return the hourly forecast.
    :param verbose: provides a more detailed log in case of error.
    :return:
    """

    url = BASE_URL + '/forecast.json'
    params = {'key': API_KEY, 'q': location}
    # the API only supports forecasts up to 14 days in the future
    if date:
        max_date = datetime.date.today() + relativedelta(days=14)
        input_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

        if input_date > max_date:
            raise ValueError('date out of range (max 14 days forecast).')

        else:
            params['dt'] = date

        console.log(f'Fetching data for location {location}...')

        response = httpx.get(url, params=params)
        response_content = response.json()
        status_code = response.status_code

        if response.is_success:
            console.log('Request successful')
            if hourly:
                table = generate_hourly_table(response_content)
                console.clear()
                console.print(table)

            else:
                print(response_content['forecast']['forecastday'][0]['day'])

        else:
            error_message = response_content['error']['message']

            if verbose:
                error_code = response_content['error']['code']
                print(f'[red][bold]ERROR {error_code} (status code {status_code}):[/bold] {error_message}[/red]')

            else:
                print(f'[red][bold]ERROR:[/bold] {error_message}[/red]')

    elif days:

        date_range: list[datetime.date] = [datetime.date.today() + relativedelta(days=i) for i in range(days)]
        params_dict_list: list[dict] = []

        for date in date_range:
            params = {'key': API_KEY, 'q': location, 'dt': date.strftime('%Y-%m-%d')}
            params_dict_list.append(params)

        response_list = asyncio.run(request_data(params_dict_list, verbose))

        table = generate_daily_table(response_list)
        console.clear()
        console.print(table)


def version_callback(value: bool):
    if value:
        print(f"[bold green]{__app_name__} version:[/bold green] {__version__}")
        raise typer.Exit()


@app.command()
def main(
        version: Annotated[
            Optional[bool], typer.Option("--version", callback=version_callback)

        ] = None,
    ):
    print(f'[bold green]Welcome to {__app_name__}![/bold green]')


if __name__ == '__main__':
    app()
