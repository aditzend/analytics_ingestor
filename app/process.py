# from audio_check import audio_info
# from transcript import transcript_data
# import logging
# import redis
# import os


# host = os.getenv('REDIS_HOST')
# port = os.getenv('REDIS_PORT')
# pool = redis.ConnectionPool(host=host, port=port, db=0)
# redis = redis.Redis(connection_pool=pool)


# logger = logging.getLogger('process')


# def mp3_process(interaction_id, path):

#     try:
#         # if status is AUDIO_CHECK then check audio
#         status = redis.get(interaction_id)
#         if status == b'AUDIO_CHECK':
#             audio_checked = audio_info(interaction_id, path)
#             if audio_checked:
#                 redis.set(interaction_id, 'GETTING_TRANSCRIPT_DATA')
#             else:
#                 redis.set(interaction_id, 'FILE_ERROR')

#         # if status is TRANSCRIPT then process transcript
#         status = redis.get(interaction_id)
#         if status == b'GETTING_TRANSCRIPT_DATA':
#             transcript_data_found = transcript_data(interaction_id)
#     except Exception as error:
#         # logger.error(f'Error in main_process: {error}')
#         logger.error(f'{interaction_id}: error')
