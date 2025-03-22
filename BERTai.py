import re
import json
from transformers import pipeline
from rank_bm25 import BM25Okapi

#Load JSON file and extract relevant content
with open('scraped_info.json', 'r') as file:
    data = json.load(file)
    
documents = [item for item in data if 'content' in item]

#Loads the question-answering pipeline
qa_pipeline = pipeline("question-answering", model="bert-large-uncased-whole-word-masking-finetuned-squad")

#Retrieves relevant context using BM25
def retrieve_relevant_context(question, documents, top_n=3):
    tokenized_docs = [doc.split() for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)
    query_tokens = question.split()
    scores = bm25.get_scores(query_tokens)

    #Select top N most relevant documents
    top_indices = scores.argsort()[-top_n:][::-1]
    return " ".join([documents[i] for i in top_indices])  

def extract_course_code(question):
    match = re.search(r'Computer Science \d{4}[A-Z]?/?[A-Z]?', question, re.IGNORECASE)
    return match.group(0) if match else None

#Answer questions
def answer_question(question, documents):
    course_code = extract_course_code(question)
    if course_code:
        filtered_docs = [doc for doc in documents if course_code in doc.get('title', '') or course_code in doc.get('content', '')]
        if filtered_docs:
            relevant_context = retrieve_relevant_context(question, [doc['content'] for doc in filtered_docs], top_n=3)
            result = qa_pipeline(question=question, context=relevant_context, max_answer_len=512)
            
            #If the answer looks too short, re-run it with more context
            if len(result['answer'].split()) < 15:  
                relevant_context = retrieve_relevant_context(question, [doc['content'] for doc in filtered_docs], top_n=5)
                result = qa_pipeline(question=question, context=relevant_context, max_answer_len=512)
                
            return validate_answer(result['answer'])

    #Fallback to all documents if no match is found
    relevant_context = retrieve_relevant_context(question, [doc['content'] for doc in documents], top_n=3)
    result = qa_pipeline(question=question, context=relevant_context, max_answer_len=512)

    #If the answer looks too short, re-run it with more context
    if len(result['answer'].split()) < 15:
        relevant_context = retrieve_relevant_context(question, [doc['content'] for doc in documents], top_n=5)
        result = qa_pipeline(question=question, context=relevant_context, max_answer_len=512)
    
    return validate_answer(result['answer'])

#Vlidate the answer
def validate_answer(answer):
    irrelevant_phrases = ["Privacy", "Web Standards", "Terms of Use", "Accessibility"]
    for phrase in irrelevant_phrases:
        if phrase in answer:
            return "Sorry, I couldn't find an answer."
    return answer


question = "What are the prerequisites for Computer Science 4447?"
answer = answer_question(question, documents)
answer = validate_answer(answer)
print(question, ": ", answer)
question = "Who is the new Canada Research Chair in Data Analytics and Digital Health in Cognitive Aging and Dementia?"
answer = answer_question(question, documents)
answer = validate_answer(answer)
print(question, ": ", answer)
question = "Do Computer Science students have acces to any free softwares?"
answer = answer_question(question, documents)
answer = validate_answer(answer)
print(question, ": ", answer)
question = "What are some sources of the department's research grants from?"
answer = answer_question(question, documents)
answer = validate_answer(answer)
print(question, ": ", answer)
question = "What Facilities does The Department of Computer Science occupy?"
answer = answer_question(question, documents)
answer = validate_answer(answer)
print(question, ": ", answer)
question = "Who won the 2024 Faculty of Science Distinguished Research Professor Award?"
answer = answer_question(question, documents)
answer = validate_answer(answer)
print(question, ": ", answer)
question = "What is Computer Science 1025 about?"
answer = answer_question(question, documents)
answer = validate_answer(answer)
print(question, ": ", answer)


