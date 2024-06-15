import streamlit as st
import boto3
import json
#file_name="hspfstyle.css"
# CSS einbinden
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("hspfstyle.css")

region = boto3.Session().region_name
session = boto3.Session(region_name=region)
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
        <h1>Campus Companion Hochschule Pforzheim</h1>
    </header>
""", unsafe_allow_html=True)

sessionId = ""

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize session id
if 'sessionId' not in st.session_state:
    st.session_state['sessionId'] = sessionId

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Willkommen beim Campus Companion, ihrem Unterstützer für alle Fragen rund um die Hochschule Pforzheim. Achtung der Chatbot befindet sich in der Betaphase und wird ausgelesen, desweiteren können verbindliche Aussagen nur von der Studierendenberatung, dem FAQ und der SPO kommen!"):

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
