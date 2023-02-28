import logging
import audio
import os
from file_manager import FileManager
from transcript import transcript_data
from job import Job
from pathlib import Path
import requests


fm = FileManager()


analytics_manager_url = os.getenv("ANALYTICS_MANAGER_URL")

logger = logging.getLogger(__name__)


# host = os.getenv("REDIS_HOST")
# port = os.getenv("REDIS_PORT")
# pool = redis.ConnectionPool(host=host, port=port, db=0)
# redis = redis.Redis(connection_pool=pool)


class CheckMp3Error(Exception):
    """File has no audio or cannot be processed"""

    pass


class TranscriptParamsError(Exception):
    """Transcript params not found"""

    pass


class PostJobError(Exception):
    """Job not posted"""

    pass


class JobPendingError(Exception):
    """Job already in progress"""

    pass


# def nlp(path: Path) -> None:
#     interaction_id = path.stem

#     # convert path to pure string
#     audio_url = str(path)
#     logger.info(f"File: {path}")
#     if path.suffix == ".mp3":
#         try:
#             check = audio.check_mp3(path)
#             if not check:
#                 raise CheckMp3Error("File has no audio or cannot be processed")
#             transcript_params = transcript_data(interaction_id=interaction_id)
#             if not transcript_params:
#                 raise TranscriptParamsError("Transcript params not found")
#             job = Job(
#                 interaction_id=interaction_id,
#                 audio_url=audio_url,
#                 audio_info=check,
#                 transcript_data=transcript_params,
#                 audio_format="mp3",
#             )
#             post_job = job.post()

#             if not post_job:
#                 raise PostJobError("Job not posted")

#         except CheckMp3Error:
#             fm.error(path=path)
#         except TranscriptParamsError:
#             fm.error(path=path)
#         except PostJobError:
#             logger.exception(f"[{interaction_id}] Job not posted")
#             fm.error(path=path)
#         else:
#             # fm.finish(path=path)
#             logger.info(f"[{interaction_id}] Job Posted")


def fail(path: Path) -> None:
    # convert path to pure stirng
    audio_url = str(path)
    logger.info(f"File: {path}")
    file_name = path.stem
    splitted_file_name = file_name.split("_", 2)
    interaction_id = ""
    if path.suffix == ".mp3" and len(splitted_file_name) == 3:
        try:
            interaction_id = splitted_file_name[2]
            fail_url = f"{analytics_manager_url}/v3/transcript/job/failed"
            requests.post(
                fail_url,
                {
                    "interaction_id": interaction_id,
                },
            )
        except IOError as error:
            logger.exception(
                f"[{interaction_id}] Job marked as failed, move to error path"
                " detected. {error}"
            )


def full(path: Path) -> None:

    # convert path to pure stirng
    audio_url = str(path)
    logger.info(f"File: {path}")
    file_name = path.stem
    splitted_file_name = file_name.split("_", 2)
    interaction_id = ""

    if path.suffix == ".mp3" and len(splitted_file_name) == 3:
        try:
            campaign_name = splitted_file_name[0]
            segment_number = splitted_file_name[1]
            interaction_id = splitted_file_name[2]
            check = audio.check_mp3(path)
            if not check:
                raise CheckMp3Error("File has no audio or cannot be processed")
            transcript_params = transcript_data(interaction_id=interaction_id)
            if not transcript_params:
                raise TranscriptParamsError("Transcript params not found")

            job = Job(
                campaign_name=campaign_name,
                segment_number=segment_number,
                interaction_id=interaction_id,
                audio_url=audio_url,
                audio_info=check,
                transcript_data=transcript_params,
                audio_format="mp3",
            )

            if job.is_pending():
                raise JobPendingError("Job already in progress")

            post_job = job.post() if not job.is_pending() else None

            if not post_job:
                raise PostJobError("Job not posted")
            else:
                logger.info(f"[{interaction_id}] Job Posted")

        except JobPendingError:
            logger.warning(f"[{interaction_id}] Job already in progress")
        except CheckMp3Error:
            fm.error(path=path)
        except TranscriptParamsError:
            fm.error(path=path)
        except PostJobError:
            logger.exception(f"[{interaction_id}] Job not posted")
            fm.error(path=path)
