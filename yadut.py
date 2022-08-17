import click
# from loguru import logger
# from functools import partial
from disk_usage.disk_usage import *
from disk_usage.reporting import total_folder_size, user_usage_df
# from disk_usage.plots import dashing_board, make_static
from disk_usage.layout import dashingboard
# from disk_usage.plots import *

##TODO:
    # Fix time format for logs written to file


@click.group()
@click.option('--level','-l',
    default='info',
    type=click.Choice(['info', 'debug']),
    show_default=True,
    help="Logging levels: [info, debug]")
def cli(level):
    logger.add(
        Path(__file__).with_suffix('.log'), 
        format="<green>{time}</green>| <blue>tid:{thread}</blue> | <red>level:{level}</red> |<level>{message}</level>",
        level=level.upper(),  
        colorize=True

        )
    pass


@cli.command()
@click.argument('input_dirs', nargs=-1)
@click.option(
    '--blocksize', '-b',
    type=int,
    default=1048576,
    show_default=True,
    help='The number of bytes to read at a time. Used if check_size =True'
    )
@click.option(
    '--maxbytes', '-m',
    type=int,
    # default=10_000_000_000,
    default=None,
    show_default=True,
    help='The max number of bytes to read. Used if check_size =True'
    )
@click.option(
    '--check_sum', '-c',
    type=bool,
    default=False,
    show_default=True,
    is_flag=True,
    help='Run checksum on if file'
    )
@click.option(
    '--threads', '-t',
    type=int,
    default=4,
    show_default=True,
    help='Number of threads'
)
@click.option(
    '--skipblocks', '-j',
    type=int,
    default=0,
    show_default=True,
    help='Skip blocks the number of blocks - (blocksize * skipblocks)'
)
@click.option(
    '--regex', '-x',
    type=str,
    default=None,
    show_default=True,
    multiple=True,
    help='Exclude files or path using regex pattern. Usage -x ".plist$" -x "/User/xxx/*'
)
@click.option(
    '--exclude', '-e',
    default=None,
    show_default=True,
    multiple=True,
    help='Exclude paths: -e /dev/ -e /etc'
)
def usage(input_dirs, check_sum, maxbytes, blocksize, threads, regex, skipblocks, exclude):
    hasher = None
    if check_sum:
        hasher = partial(filehash, maxbytes=maxbytes,
                         blocksize=blocksize, skipblocks=skipblocks)
    dirin = []
    create_db_and_tables('replace')
    if regex:
        exclude_pat = exclude_pattern(regex)
    else:
        exclude_pat =None
    if exclude:
        exclude = [Path(x).resolve() for x in exclude]
    for directory in input_dirs:
        path = Path(directory)
        if not path.exists():
            logger.info(f'Skipped: {path} does not exists')
            continue
        logger.debug(f'{path} Added path to list')
        dirin.append(path)
    
    queue = Queue()
    add_to_q(queue, dirin)

    for w in worker(threads, queue, hasher=hasher, 
                    exclude_regex=exclude_pat, exclude=exclude):
        logger.info(f'Starting procssing threads {w}')
        w.join()


@cli.command()
def report():
    total_folder_size()

@cli.command()
@click.option(
    '--port','-p', 
    type = int,
    show_default=True,
    default=8050,
    help='Port number to start the port on'
)
@click.option(
    '--debug', '-d',
    is_flag=True,
    show_default=True,
    default=False,
    help='Flask Server debuging'
)
def dashboard(port, debug):
    """hopefully a interactive dashboard generated using ploty and dashly"""
    app = dashingboard()
    from waitress import serve
    app.run(
        debug=debug,
        port=port,
        host='0.0.0.0'
        )

if __name__ == "__main__":
    cli() 
