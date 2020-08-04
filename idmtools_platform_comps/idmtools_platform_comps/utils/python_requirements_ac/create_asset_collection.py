import os
import sys
from hashlib import md5

from COMPS import Client
from COMPS.Data import AssetCollectionFile, QueryCriteria
from COMPS.Data import Experiment
from COMPS.Data.AssetCollection import AssetCollection

MD5_KEY = 'idmtools-requirements-md5'
AC_FILE = 'ac_info.txt'
LIBRARY_ROOT_PREFIX = 'L'


def calculate_md5(file_path) -> str:
    """
    Calculate and md5
    """
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            md5calc = md5()
            md5calc.update(f.read())
            md5_checksum_str = md5calc.hexdigest()
        return md5_checksum_str


def build_asset_file_list(comps_sim, prefix=LIBRARY_ROOT_PREFIX):
    """
    Utility function to build all library files
    Args:
        comps_sim: given simulation
        prefix: used to identify library files

    Returns: file paths as a list
    """

    output = []
    for root, _, filenames in os.walk(prefix):
        for filename in filenames:
            asset = AssetCollectionFile(file_name=os.path.basename(filename),
                                        relative_path=os.path.join("site-packages", root.replace(prefix, "").strip("/")).strip("/"),
                                        md5_checksum=calculate_md5(os.path.join(root, filename))
                                        )
            output.append(asset)

    return output


def get_first_simulation_of_experiment(exp_id):
    """
    Retrieve the first simulation from an experiment
    Args:
        exp_id: use input (experiment id)

    Returns: list of files paths
    """
    comps_exp = Experiment.get(exp_id)
    comps_sims = comps_exp.get_simulations(QueryCriteria().select_children('hpc_jobs'))
    comps_sim = comps_sims[0]

    return comps_sim


def main():
    print(sys.argv)

    if len(sys.argv) < 3:
        raise Exception(
            "The script needs to be called with `python <model.py> <experiment_id> <md5_str> <endpoint>'.\n{}".format(
                " ".join(sys.argv)))

    # Get the experiments
    exp_id = sys.argv[1]
    print('exp_id: ', exp_id)

    # Get mds
    md5_str = sys.argv[2]
    print('md5_str: ', md5_str)

    # Get endpoint
    endpoint = sys.argv[3]
    print('endpoint: ', endpoint)

    client = Client()
    client.login(endpoint)

    # Retrieve the first simulation of the experiment
    comps_sim = get_first_simulation_of_experiment(exp_id)
    print('sim_id: ', comps_sim.id)

    # Build files metadata
    base_path = os.path.join(comps_sim.hpc_jobs[-1].working_directory, LIBRARY_ROOT_PREFIX)
    asset_files = build_asset_file_list(comps_sim, prefix=base_path)
    print('asset files count: ', len(asset_files))

    # Output files
    max_files = 10
    print('Display the fist 10 files:\n', "\n".join([f"{a.relative_path}/{a.file_name}" for a in asset_files[0:max_files]]))

    ac = AssetCollection()
    tags = {MD5_KEY: md5_str}
    ac.set_tags(tags)

    # Create asset collection
    for af in asset_files:
        ac.add_asset(af)

    sys.stdout.flush()
    missing_files = ac.save(return_missing_files=True)

    # If COMPS responds that we're missing some files, then try creating it again,
    # uploading only the files that COMPS doesn't already have.
    if missing_files:

        ac2 = AssetCollection()
        ac2.set_tags(tags)

        for acf in ac.assets:
            if acf.md5_checksum in missing_files:
                rp = acf.relative_path
                fn = acf.file_name
                acf2 = AssetCollectionFile(fn, rp, tags=acf.tags)
                rfp = os.path.join(base_path, rp.replace("site-packages", "").strip(os.path.sep), fn)
                ac2.add_asset(acf2, rfp)
            else:
                ac2.add_asset(acf)

        print("\n\n\n=====================\nUploading files not in comps: " + "\n".join(
            [f"{a.relative_path}/{a.file_name}" for a in ac2.assets if a.md5_checksum is None]))
        sys.stdout.flush()
        ac2.save()
        ac = ac2
    # Output ac
    print('ac_id: ', ac.id)

    # write ac_id to file ac_info.txt
    with open(AC_FILE, 'w') as outfile:
        outfile.write(str(ac.id))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
