import logging
import boto3
import urllib3
import json
import openai
import uuid

# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients setup
transcribe_client = boto3.client('transcribe')
s3_client = boto3.client('s3')
http = urllib3.PoolManager()

openai.api_key = 'YOUR_OPENAI_API_KEY'


def lambda_handler(event, context):
    try:
        audio_file_path = f"s3://{event['Records'][0]['s3']['bucket']['name']}/{event['Records'][0]['s3']['object']['key']}"
        transcribed_text = transcribe_audio(audio_file_path)
        summary = summarize_text_with_chatgpt(transcribed_text)

        return {
            'statusCode': 200,
            'body': {
                'summary': summary
            }
        }
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return {
            'statusCode': 500,
            'body': f"Failed to process audio: {e}"
        }


def transcribe_audio(audio_file_path):
    # Generating a unique job name
    job_name = f"transcription-job-{uuid.uuid4()}"
    logger.info(f"Starting transcription for audio file: {audio_file_path}")

    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': audio_file_path},
        MediaFormat='mp3',
        LanguageCode='en-US'
    )

    while True:
        status = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break

    logger.info(
        f"Transcription job status: {status['TranscriptionJob']['TranscriptionJobStatus']}")

    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'FAILED':
        raise Exception("Transcription job failed.")

    transcribed_text_location = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
    transcribed_data = http.request('GET', transcribed_text_location).data
    transcribed_text = json.loads(transcribed_data)[
        'results']['transcripts'][0]['transcript']

    return transcribed_text


def summarize_text_with_chatgpt(transcribed_text):
    logger.info("Sending transcribed text to ChatGPT for summarization")

    # Creating a prompt to guide ChatGPT's response
    prompt_text = (
        "You are an understandable and encouraging teacher. "
        "Please provide a clear and motivating summary of the following content:\n\n"
        f"{transcribed_text}"
    )

    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=prompt_text,
        max_tokens=600
    )

    summary = response['choices'][0]['text'].strip()

    if summary:
        logger.info("Successfully received summary from ChatGPT")
        return summary
    else:
        raise Exception("Failed to summarize the text with ChatGPT.")
