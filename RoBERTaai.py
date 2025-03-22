import re
import json
from transformers import pipeline
from rank_bm25 import BM25Okapi

#Load JSON file and extract relevant content
with open('scraped_info.json', 'r') as file:
    data = json.load(file)

documents = [item for item in data if 'content' in item]

#Load the question-answering pipeline with RoBERTa
qa_pipeline = pipeline("question-answering", model="deepset/roberta-large-squad2")

#Retrieve relevant context using BM25
def retrieve_relevant_context(question, documents, top_n=5):  
    tokenized_docs = [doc.split() for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)
    query_tokens = question.split()
    scores = bm25.get_scores(query_tokens)

    #Select top N most relevant documents
    top_indices = scores.argsort()[-top_n:][::-1]
    relevant_context = " ".join([documents[i] for i in top_indices])
    return relevant_context

def extract_course_code(question):
    match = re.search(r'Computer Science \d{4}[A-Z]?/?[A-Z]?', question, re.IGNORECASE)
    return match.group(0) if match else None

#Answer questions
def answer_question(question, documents):
    course_code = extract_course_code(question)
    if course_code:
        filtered_docs = [doc for doc in documents if course_code in doc.get('title', '') or course_code in doc.get('content', '')]
        if filtered_docs:
            relevant_context = retrieve_relevant_context(question, [doc['content'] for doc in filtered_docs], top_n=5)
            result = qa_pipeline(question=question, context=relevant_context, max_answer_len=512)
            
            #If the answer looks too short or doesn't seem relevant, re-run it with more context
            if len(result['answer'].split()) < 3 or not is_answer_relevant(question, result['answer'], relevant_context):  
                relevant_context = retrieve_relevant_context(question, [doc['content'] for doc in filtered_docs], top_n=7) 
                result = qa_pipeline(question=question, context=relevant_context, max_answer_len=512)
                
            return result['answer']

    relevant_context = retrieve_relevant_context(question, [doc['content'] for doc in documents], top_n=5)  
    result = qa_pipeline(question=question, context=relevant_context, max_answer_len=512)

    #If the answer looks too short or doesn't seem relevant, re-run it with more context
    if len(result['answer'].split()) < 3 or not is_answer_relevant(question, result['answer'], relevant_context):
        relevant_context = retrieve_relevant_context(question, [doc['content'] for doc in documents], top_n=7) 
        result = qa_pipeline(question=question, context=relevant_context, max_answer_len=512)
    
    return result['answer']

#Validate the answer
def validate_answer(answer, question, context):
    #Check if the answer is too short or looks off
    if not answer or len(answer.strip()) < 3:
        return "I don't know"
    
    #Check if the answer is relevant to the context
    if is_answer_relevant(question, answer, context):
        return answer
    
    return "I don't know"

#Check if the generated answer is relevant to the question and context
def is_answer_relevant(question, answer, context):
    question_terms = set(question.lower().split())
    answer_terms = set(answer.lower().split())

    #If the answer contains key terms from the question, it may be relevant
    if question_terms.intersection(answer_terms):
        return True

    context_terms = set(context.lower().split())
    if answer_terms.intersection(context_terms):
        return True
    
    if len(answer.split()) <= 2 and any(term in answer.lower() for term in question_terms):
        return True

    #If the answer doesn't  to address the question, return False
    return False


question = "Do Computer Science students have access to any free software?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "What time does Computer Science 4490 start?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "Who are the members of the Computer Science student council?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "Who won the 2024 Faculty of Science Distinguished Research Professor Award?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "Who is the new Canada Research Chair in Data Analytics and Digital Health in Cognitive Aging and Dementia?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "What is the average class size for upper-level Computer Science courses?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "What types of extracurricular activities and clubs does the Computer Science department offer?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "What are the prerequisites for Computer Science 4447?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "Do Computer Science students have acces to any free softwares?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "What are some sources of the department's research grants from?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "What Facilities does The Department of Computer Science occupy?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)

question = "What is Computer Science 1025 about?"
answer = answer_question(question, documents)
print("Question:", question)
print("Answer:", answer)
