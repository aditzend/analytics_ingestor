import requests
import logging
import os
import alert


logger = logging.getLogger(__name__)


"""
Get transcript data from dbinterface
No spanish names allowed in the return value
Parameters get unrolled and saved as keys in the return value

Example of return value :
{
    'INTERACTION_ID': interaction_id,
    'ASR_PROVIDER': 'WHISPER',
    'ASR_LANGUAGE': 'es'
}
"""


class InteractionNotFound(Exception):
    """Interaction was not found in database"""

    pass


def transcript_data(interaction_id: str):
    logger.info(f"[{interaction_id}] Getting transcript data")
    dbinterface_url = os.getenv("DBINTERFACE_URL")
    try:
        result = requests.get(
            f"{dbinterface_url}/v3/transcript_data/{interaction_id}"
        )
        if result.status_code != 200:
            raise InteractionNotFound("Interaction not found in database")

        # save all NombreParametro in parameters as keys and Valor as values
        parameters = result.json()["parameters"]
        res = {
            "INTERACTION_ID": interaction_id,
        }
        for parameter in parameters:
            res[parameter["NombreParametro"]] = parameter["Valor"]
            logger.info(
                f" [{interaction_id}] PARAMETER"
                f' {parameter["NombreParametro"]}'
                f': {parameter["Valor"]}'
            )
        return res

    except InteractionNotFound as error:
        logger.exception(f"[{interaction_id}] Not found in database")
        alert.error(interaction_id, error)

    except ConnectionError as error:
        logger.exception(f"[{interaction_id}] Connection error")
        alert.error(interaction_id, error)

    except ValueError as error:
        logger.exception(f"[{interaction_id}] Value error")
        alert.error(interaction_id, error)

    except KeyError as error:
        logger.exception(f"[{interaction_id}] Key error")
        alert.error(interaction_id, error)
