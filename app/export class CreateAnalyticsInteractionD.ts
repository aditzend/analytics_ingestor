export class CreateAnalyticsInteractionDto {
  idInteraccion: string;
  estado: string;
  sentimientoPrincipal: string;
  emocionPrincipal: string;
  intencionPrincipal: string;
  subIntencionPrincipal: string;
  hayHateSpeech: boolean;
  haySentimientoNegativo: boolean;
  hayAlegria: boolean;
  hayDisgusto: boolean;
  hayMiedo: boolean;
  hayIra: boolean;
  haySorpresa: boolean;
  hayTristeza: boolean;
  entidades: string;
}


        message = (
            {
                "interaction_id": j.interaction_id,
                "status": "ALL_FINISHED",
                "transcription": {
                    "transcription_job_id": j.transcription_job_id,
                    "base_path": j.base_path,
                    "audio_url": j.audio_url,
                    "asr_provider": j.asr_provider,
                    "asr_language": j.asr_language,
                    "sample_rate": j.sample_rate,
                    "num_samples": j.num_samples,
                    "channels": j.channels,
                    "audio_format": j.audio_format,
                    "is_silent": j.is_silent,
                    "utterances": j.utterances,
                },
                "events": result.events,
                "nlp": {
                    "pipeline": "default",
                    "main_sentiment": result.main_sentiment,
                    "main_emotion": result.main_emotion,
                    "main_intent_group": result.main_intent_group,
                    "main_intent_subgroup": result.main_intent_subgroup,
                    "hate_speech_flag": result.hate_speech_flag,
                    "neg_sentiment_flag": result.neg_sentiment_flag,
                    "joy_emotion_flag": result.joy_emotion_flag,
                    "sadness_emotion_flag": result.sadness_emotion_flag,
                    "surprise_emotion_flag": result.surprise_emotion_flag,
                    "fear_emotion_flag": result.fear_emotion_flag,
                    "anger_emotion_flag": result.anger_emotion_flag,
                    "disgust_emotion_flag": result.disgust_emotion_flag,
                    "entities": result.entities,
                },
          },
          
          export class CreateAnalyticsEventDto {
  idEvento: string;
  idInteraccion: string;
  idSegmento: string;
  tipo: string;
  comienzo: number;
  fin: number;
  texto: string;
  intencion: string;
  entidades: string;
  sentimientos: string;
  emociones: string;
  ner: string;
  pos: string;
  hateSpeech: string;
          }



                event = {
                    "text": utterance.text,
                    "interaction_id": j.interaction_id,
                    "segment_id": j.interaction_id + "-s1",
                    "event_id": event_id,
                    "type": "utterance",
                    "start": utterance.start,
                    "end": utterance.end,
                    "nlp": {
                        "intent": intent,
                        "entities": intent["entities"],
                        "sentiment": nlp["sentiment"],
                        "emotion": nlp["emotion"],
                        "ner": nlp["ner"],
                        "pos": nlp["pos"],
                        "hate_speech": nlp["hate_speech"],
                    },
                }