import streamlit as st
import boto3
import json
region = 'us-east-1'
# CSS einbinden
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("hspfstyle.css")

# Ensure your region and credentials are set correctly
aws_access_key_id = "AKIA4MTWK35ML3TMH5C3"
aws_secret_access_key = "7whjY6uW9z6GPJGkUZR1x/BDLXgvjZoC173KfAs1"
region = "us-east-1"

session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region
)

lambda_client = session.client('lambda')

# Function to generate presigned URL for S3 object
def generate_presigned_url(bucket_uri):
    s3 = boto3.client('s3')
    try:
        bucket_name, key = bucket_uri.split('/', 2)[-1].split('/', 1)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=3600  # URL expires in 1 hour
        )
        return presigned_url
    except Exception as e:
        st.error(f"Error generating presigned URL: {e}")
        return None

# Header mit Logo und Titel
st.markdown("""
    <header>
        <img src="https://www.hs-pforzheim.de/typo3conf/ext/wr_hspfo/Resources/Public/Images/logo-white.svg" alt="Hochschule Pforzheim Logo">
        <h1 class="text-color">Campus Companion Hochschule Pforzheim</h1>
    </header>
""", unsafe_allow_html=True)

sessionId = ""

# Initialize chat history with welcome message
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": (
            "Willkommen beim Campus Companion, Ihrem Unterstützer für alle Fragen rund um die Hochschule Pforzheim. "
            "Achtung: Der Chatbot befindet sich in der Betaphase und wird ausgelesen. Des Weiteren können verbindliche Aussagen "
            "nur von der Studierendenberatung, dem FAQ und der SPO kommen!"
        )}
    ]

# Initialize session id
if 'sessionId' not in st.session_state:
    st.session_state['sessionId'] = sessionId

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Was ist los?"):

    # Display user input in chat message container
    question = prompt
    st.chat_message("user").markdown(question)

    # Call lambda function to get response from the model
    payload = json.dumps({"question": prompt, "sessionId": st.session_state['sessionId']})
    result = lambda_client.invoke(
                FunctionName='InvokeKnowledgeBase',
                Payload=payload
            )

    result = json.loads(result['Payload'].read().decode("utf-8"))
    answer = result['body']['answer']
    sessionId = result['body']['sessionId']
    citations = result['body']['citations']

    st.session_state['sessionId'] = sessionId

    # Add user input to chat history
    st.session_state.messages.append({"role": "user", "content": question})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(answer)

        # Add citation links at the end of the response
        if citations:
            with st.expander("Zitierungen anzeigen"):
                for citation in citations:
                    for reference in citation['retrievedReferences']:
                        document_name = reference['location']['s3Location']['uri']
                        st.markdown(f"**Dokument:** {document_name}")
                        help_text = reference['content']['text']
                        st.markdown(help_text)
                    display_text = citation['generatedResponsePart']['textResponsePart']['text']
                    st.markdown(display_text)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": answer})
