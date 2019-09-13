import logging
import os
from typing import Optional, List, Tuple
import pandas as pd
from flask import request
from flask_restful import Resource, reqparse, abort
from sqlalchemy import String
from idmtools_platform_local.workers.data.job_status import JobStatus
from idmtools_platform_local.workers.database import get_session
from idmtools_platform_local.status import Status
from idmtools_platform_local.workers.ui.config import db
from idmtools_platform_local.workers.ui.controllers.utils import validate_tags

logger = logging.getLogger(__name__)


def sim_status(id: Optional[str], experiment_id: Optional[str], status: Optional[str],
               tags: Optional[List[Tuple[str, str]]], page:int = 1, per_page:int = 50) -> pd.DataFrame:
    """
    List of statuses for simulation(s) with the ability to filter by id, experiment_id, status, and tags

    Args:
        id (Optional[str]): Optional Id of simulation
        experiment_id (Optional[str]): Optional experiment id
        status (Optional[str]): Optional status string to filter by
        tags (Optional[List[Tuple[str, str]]]): Optional list of tuples in form of tag_name tag_value to user to filter
            experiments with

    Returns:
        None
    """
    session = db.session
    # Simulations ALWAYS have a parent
    criteria = [JobStatus.parent_uuid != None]  # noqa: E711

    # start building our filter criteria
    if id is not None:
        criteria.append(JobStatus.uuid == id)

    if experiment_id is not None:
        criteria.append(JobStatus.parent_uuid == experiment_id)

    if status is not None:
        criteria.append(JobStatus.status == Status[status])

    if tags is not None:
        for tag in tags:
            criteria.append((JobStatus.tags[tag[0]].astext.cast(String) == tag[1]))

    query = session.query(JobStatus).filter(*criteria)\
        .order_by(JobStatus.uuid.desc(), JobStatus.parent_uuid.desc()).paginate(page, per_page)
    total = query.total

    return list(map(lambda x: x.to_dict(False), query.items)), total


status_strs = [str(status) for status in Status]
idx_parser = reqparse.RequestParser()
idx_parser.add_argument('experiment_id', help='Experiment ID', default=None)
idx_parser.add_argument('status', help='Status to filter by. Should be one of the following '
                                       '{}'.format(','.join(status_strs)),
                        choices=status_strs,
                        default=None)
idx_parser.add_argument('page', type=int, default=1, help="Page")
idx_parser.add_argument('per_page', type=int, default=50, help="Per Page")
idx_parser.add_argument('tags', action='append', default=None,
                        help="Tags tio filter by. Tags must be in format name,value")


class Simulations(Resource):
    def get(self, id=None):
        args = idx_parser.parse_args()
        args['id'] = id

        validate_tags(args['tags'])

        result, total = sim_status(**args)

        if id:
            if not result:
                abort(404, message=f"Could not find simulation with id {id}")
            return result[0]
        return result, 200, {'X-Total': total, 'X-Per-Page': args.per_page}

    def put(self, id):
        data = request.json()
        # at moment, only allow status to be updated(ie canceled'
        # later, we may support resuming but we will need to include more data in the db to do this
        data = {k: v for k, v in data.items() if k == 'status' and v in ['canceled']}
        if len(data) > 0:
            s = get_session()
            current_job: JobStatus = s.query(JobStatus).filter(JobStatus.uuid == id).first()
            # check if we have a PID, if so kill it
            if current_job.metadata is not None and 'pid' in current_job.metadata:
                try:
                    os.killpg(current_job.metadata['pid'], 9)
                except Exception as e:
                    logger.exception(e)
            current_job.__dict__.update(data)
            s.add(current_job)
            s.commit()
        else:
            abort(400, message='Currently the only allowed simulation update is canceling a simulation')
