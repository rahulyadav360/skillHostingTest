from ask_sdk_core.dispatch_components import (AbstractRequestHandler, AbstractExceptionHandler, AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name, get_supported_interfaces

from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective, ExecuteCommandsDirective, SpeakItemCommand, HighlightMode
)

import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def supports_apl(handler_input):

    supported_interfaces = get_supported_interfaces(
        handler_input)
    return supported_interfaces.alexa_presentation_apl != None

def _load_apl_document(file_path):

    with open(file_path) as f:
        logger.debug(f)
        return json.load(f)

questionBank = {
  1: { "questionData": {
            "question": "What is a no-claim bonus? ",
            "option1": "Benefit for those who have not claimed insurance during the preceding 1 year of cover.",
            "option2": "Benefit for those who have not claimed insurance during the preceding 10 year of cover.",
            "option3": "Benefit for those who have not claimed insurance during the preceding 5 year of cover."
            }
    },
  2: { "questionData": {
            "question": "Who is a beneficiary? ",
            "option1": "Beneficiary is the one who is nominated for the insured amount in case of death.",
            "option2": "Beneficiary is the one who takes the policy.",
            "option3": "Beneficiary is the sales agent."
            }
    },
  3: { "questionData": {
            "question": "What do you mean by term Annuity? ",
            "option1": "Regular amount paid by the insurance company to the insured, after a certain period.",
            "option2": "The premium of the policy.",
            "option3": "Amount paid in case of death."
            }
    },
  4: { "questionData": {
            "question": "What does the term Indemnity mean? ",
            "option1": "Used to cover the loss or damage claimed by another person.",
            "option2": "Amount paid out in case of death.",
            "option3": "Refusal to pay the policy premium."
            }
    },
  5: { "questionData": {
            "question": "What is an Endowment Policy? ",
            "option1": "Combination of saving along with risk cover.",
            "option2": "Life term policy.",
            "option3": "Life long policy."
            }
    }
}

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
        
    def handle(self, handler_input):
        logger.info("In LaunchRequestHandler")
        
        session_attributes = handler_input.attributes_manager.session_attributes
        speech_output = "Hey there! Welcome to the employee assessment test. I will ask you a few multiple choice questions related to insurance policies and you need to answer them in the least number of tries possible. Are you ready?"
        reprompt = "Are you ready to start the assessment?"
        session_attributes['repeat_speech_output'] = speech_output
        session_attributes['repeat_reprompt'] = reprompt
        session_attributes['question_number'] = 1
        handler_input.attributes_manager.session_attributes = session_attributes
        
        if supports_apl(handler_input):
            handler_input.response_builder.add_directive(
                RenderDocumentDirective(
                    token = "simpleDisplayTemplate",
                    document = _load_apl_document('simpleDisplayTemplate.json'),
                    datasources = {"message": {"text": speech_output}}
                    )
                )
        
        return handler_input.response_builder.speak(speech_output).ask(reprompt).response

class YesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.YesIntent")(handler_input)
        
    def handle(self, handler_input):
        logger.info("In YesIntentHandler")
        session_attributes = handler_input.attributes_manager.session_attributes
        question_number = session_attributes['question_number']
        speech_output = "Alright. Here's the first question. <break time='1s'/>" + questionBank[question_number]["questionData"]["question"] + "Your options are: A. " + questionBank[question_number]["questionData"]["option1"] + "<break time='0.7s'/> B. " + questionBank[question_number]["questionData"]["option2"] + "<break time='0.7s'/> or C. " + questionBank[question_number]["questionData"]["option3"]
        reprompt = "Whats your answer? A. B. or C.?"
        if supports_apl(handler_input):
            handler_input.response_builder.add_directive(
                RenderDocumentDirective(
                    token = "displayQuestionTemplate",
                    document = _load_apl_document('questionTemplate.json'),
                    datasources = questionBank[question_number]
                    )
                )
        session_attributes['repeat_speech_output'] = speech_output
        session_attributes['repeat_reprompt'] = reprompt
        session_attributes['number_of_attempts'] = 0
        handler_input.attributes_manager.session_attributes = session_attributes
        
        return handler_input.response_builder.speak(speech_output).ask(reprompt).response


class AnswerIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AnswerIntent")(handler_input)
        
    def handle(self, handler_input):
        logger.info("In AnswerIntentHandler")
        session_attributes = handler_input.attributes_manager.session_attributes
        question_number = session_attributes['question_number']
        number_of_attempts = session_attributes['number_of_attempts'] + 1
        users_choice = handler_input.request_envelope.request.intent.slots['option'].resolutions.resolutions_per_authority[0].values[0].value.name
        print(type(users_choice))
        print(users_choice)
        if int(question_number) < 5:
            if users_choice == "A":
                question_number += 1
                speech_output = "That's the correct answer. The next question is: <break time='1s'/>" + questionBank[question_number]["questionData"]["question"] + "The options are: A. " + questionBank[question_number]["questionData"]["option1"] + "<break time='0.7s'/> B. " + questionBank[question_number]["questionData"]["option2"] + "<break time='0.7s'/> or C. " + questionBank[question_number]["questionData"]["option3"]
                reprompt = "Whats your answer? A. B. or C.?"
            else:
                speech_output = "Sorry, that answer is incorrect. Try again."
                reprompt = "Whats your answer? A. B. or C.?"
            
        elif int(question_number) == 5:
            if users_choice == "A":
                speech_output = "That's the correct answer. "
                accuracy = int(500/number_of_attempts)
                if accuracy >= 60:
                    speech_output = speech_output + "This brings us to the end of the assessment. With an accuracy of " + str(accuracy) + " percent, you have passed with flying colours. Goodbye."
                else:
                    speech_output = speech_output + "This brings us to the end of the assessment. Unfortunately, you have failed the assessment due to poor accuracy of " + str(accuracy) + " percent. Goodbye."
                if supports_apl(handler_input):
                    handler_input.response_builder.add_directive(
                        RenderDocumentDirective(
                            token = "simpleDisplayTemplate",
                            document = _load_apl_document('simpleDisplayTemplate.json'),
                            datasources = {"message": {"text": speech_output}}
                            )
                        )
                return handler_input.response_builder.speak(speech_output).set_should_end_session(True).response
                
            else:
                speech_output = "Sorry, that answer is incorrect. Try again."
                reprompt = "Whats your answer? A. B. or C.?"
        
        session_attributes['repeat_speech_output'] = speech_output
        session_attributes['repeat_reprompt'] = reprompt
        session_attributes['question_number'] = question_number
        session_attributes['number_of_attempts'] = number_of_attempts
        handler_input.attributes_manager.session_attributes = session_attributes
        
        if supports_apl(handler_input):
            handler_input.response_builder.add_directive(
                RenderDocumentDirective(
                    token = "displayQuestionTemplate",
                    document = _load_apl_document('questionTemplate.json'),
                    datasources = questionBank[question_number]
                    )
                )
        
        return handler_input.response_builder.speak(speech_output).ask(reprompt).response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)
        
    def handle(self, handler_input):
        logger.info("In HelpIntentHandler")
        speech_output = "This is the help intent."
        return handler_input.response_builder.speak(speech_output).ask(speech_output).response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            is_intent_name("AMAZON.CancelIntent")(handler_input) or
            is_intent_name("AMAZON.StopIntent")(handler_input)
            )
        
    def handle(self, handler_input):
        logger.info("In CancelOrStopIntentHandler")
        speech_output = "Goodbye."
        return handler_input.response_builder.speak(speech_output).set_should_end_session(True).response

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)
        
    def handle(self, handler_input):
        logger.info("In FallbackIntentHandler")
        speech_output = "This is the fallback intent."
        return handler_input.response_builder.speak(speech_output).ask(speech_output).response


class NoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.NoIntent")(handler_input)
        
    def handle(self, handler_input):
        logger.info("In NoIntentHandler")
        speech_output = "Okay. You can come back later whenever you are ready."
        if supports_apl(handler_input):
            handler_input.response_builder.add_directive(
                RenderDocumentDirective(
                    token = "simpleDisplayTemplate",
                    document = _load_apl_document('simpleDisplayTemplate.json'),
                    datasources = {"message": {"text": speech_output}}
                    )
                )
        return handler_input.response_builder.speak(speech_output).set_should_end_session(True).response
class RepeatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.RepeatIntent")(handler_input)
        
    def handle(self, handler_input):
        logger.info("In RepeatIntentHandler")
        session_attributes = handler_input.attributes_manager.session_attributes
        speech_output = session_attributes['repeat_speech_output']
        reprompt = session_attributes['repeat_reprompt']
        return handler_input.response_builder.speak(speech_output).ask(speech_output).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)
        
    def handle(self, handler_input):
        logger.info("In SessionEndedRequestHandler")
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True
        
    def handle(self, handler_input, exception):
        logger.error(exception, exc_info = True)
        speech_output = "Sorry, I had trouble doing what you asked. Please try again."
        return handler_input.response_builder.speak(speech_output).ask(speech_output).response

class RequestLogger(AbstractRequestInterceptor):
    def process(self, handler_input):
        #logger.debug("Alexa Request: {}".format(handler_input.request_envelope.request))
        pass

class ResponseLogger(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        #logger.debug("Alexa Response: {}".format(response))
        pass

sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(RepeatIntentHandler())
sb.add_request_handler(AnswerIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

lambda_handler = sb.lambda_handler()