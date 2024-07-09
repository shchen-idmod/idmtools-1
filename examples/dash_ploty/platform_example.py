import os

import pandas as pd

from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from datetime import datetime

job_directory = "C:\github\idmtools\examples\dash_ploty\inputs"
# Define FILE Platform.
platform = Platform('FILE', job_directory=job_directory)
suite = platform.get_item("d78c7302-ddf6-443d-b3e0-a619023596c1", ItemType.SUITE)
exp = platform.get_item("b8c6b0c5-5ff3-45e5-99d0-fb2921297cbb", ItemType.EXPERIMENT)
#sim_dir = platform.get_directory_by_id("0ee75c59-9c28-49c5-ac29-5d77bc61c261", ItemType.SIMULATION)
simulations = exp.simulations
status_dict = {}

df = pd.DataFrame(columns=['sim_id', 'status', 'last_modified', 'insetchart_exists'])
for sim in simulations:
    insetchart_exists = False
    sim_dir = platform.get_directory(sim)
    last_modified = datetime.fromtimestamp(os.path.getmtime(sim_dir)).strftime('%Y-%m-%d %H:%M:%S')
    job_status_path = sim_dir.joinpath("job_status.txt")
    if not job_status_path.exists():
        status_dict[sim.id] = "pending"
    else:
        status = open(job_status_path).read().strip()
        if status == '0':
            status_dict[sim.id] = "succeeded"
            insetchart_path = sim_dir.joinpath("output/insetchart.json")
            if not insetchart_path.exists():
                insetchart_exists = False
            else:
                insetchart_exists = True
        elif status == '100':
            status_dict[sim.id] = "running"
        elif status == '-1':
            status_dict[sim.id] = "failed"
        else:
            status_dict[sim.id] = "running"

    list = [sim.id, status_dict[sim.id], last_modified, insetchart_exists]
    ser = pd.Series(list, index=['sim_id', 'status', 'last_modified', 'insetchart_exists'])
    df = pd.concat([df, pd.DataFrame([ser])], ignore_index=True)
print(df)