import logging
import boto3
import urllib3
import uuid

# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients setup
transcoder_client = boto3.client('elastictranscoder')
s3_client = boto3.client('s3')
http = urllib3.PoolManager()

INPUT_BUCKET = 'video-audio-extraction-bucket'


def lambda_handler(event, context):
    video_link = event.get('videoLink')

    try:
        # Download video from the provided link
        video_data = download_video(video_link)
        video_file_name = video_link.split('/')[-1]

        # Upload video to S3 bucket
        upload_to_s3(video_data, video_file_name)

        # Extract audio using Elastic Transcoder
        extract_audio(video_file_name)

        return {
            'statusCode': 200,
            'body': "Audio extraction initiated."
        }

    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': f"Failed to process video: {e}"
        }


def download_video(url):
    response = http.request('GET', url)
    if response.status != 200:
        raise ValueError(f"Failed to download video from URL: {url}")
    return response.data


def upload_to_s3(data, file_name):
    s3_client.put_object(Bucket=INPUT_BUCKET, Key=file_name, Body=data)
    logger.info(f"Uploaded video {file_name} to S3 bucket {INPUT_BUCKET}")


def extract_audio(video_file_name):
    pipeline_id = '1698955870462-yilayh'
    preset_id = '1351620000001-300040'  # MP3 audio extraction preset ID
    # Generating a unique job name
    unique_job_name = f"audio-extraction-{uuid.uuid4()}"

    logger.info(f"Extracting audio for video: {video_file_name}")

    job = transcoder_client.create_job(
        PipelineId=pipeline_id,
        Input={'Key': video_file_name},
        Output={
            'Key': f"{unique_job_name}.mp3",
            'PresetId': preset_id
        }
    )

    logger.info(
        f"Audio extraction job started with job ID: {job['Job']['Id']}")
