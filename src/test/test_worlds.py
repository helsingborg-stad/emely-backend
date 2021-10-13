from src.chat.worlds import ChatWorld, InterviewWorld, FikaWorld
from src.api.bodies import BrainMessage, UserMessage, InitBody


class TestOldJsonSchema:

    @classmethod
    def setup_class(cls):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.fworld = FikaWorld()
        cls.iworld = InterviewWorld()

        fika_init = {
            "name": "Pytest",
            "created_at": '1999-04-07 18:59:24.584658',
            "persona": "fika",
            "development_testing": True,
            "webapp_local": True,
            "webapp_url": "pytest",
            "webapp_version": "NA",
            "brain_url": "NA",
            "lang": "sv",
            "user_ip_number": "127.0.0.1",
            }

        interview_init = {
            "name": "Pytest",
            "job": "Pytest",
            "created_at": '1999-04-07 18:59:24.584658',
            "persona": "intervju",
            "development_testing": True,
            "webapp_local": True,
            "webapp_url": "pytest",
            "webapp_version": "NA",
            "brain_url": "NA",
            "lang": "sv",
            "user_ip_number": "127.0.0.1",
            }

        fika_msg = {
            "message": "This is a test message you can change",
            "conversation_id": "__CHANGE_ME__",
            "response_time": -1,
            "created_at": "1999-04-07 18:59:24.584658",
            "recording_used": False,
            "lang": "sv",
            "password": "KYgZfDG6P34H56WJM996CKKcNG4"
                    }
        
        interview_msg = {
            "message": "This is a test message you can change",
            "conversation_id": "__CHANGE_ME__",
            "response_time": -1,
            "created_at": "1999-04-07 18:59:24.584658",
            "recording_used": False,
            "lang": "en",
            "password": "KYgZfDG6P34H56WJM996CKKcNG4"
                        }

        cls.build_data = {'brain_version': 'lol no idea it does not matter', 'brain_url': 'lol idk'}
        cls.fika_init = InitBody(**fika_init)
        cls.interview_init = InitBody(**interview_init)
        cls.fika_msg = UserMessage(**fika_msg)
        cls.interview_msg = UserMessage(**interview_msg)


    def test_init_fika(self):
        self.fworld.init_conversation(self.fika_init, self.build_data)
        
        
    def test_init_interview(self):
        self.iworld.init_conversation(self.interview_init, self.build_data)


    def test_message_fika(self):
        fika_response = self.fworld.init_conversation(self.fika_init, self.build_data)
        conversation_id = fika_response.conversation_id

        fika_msg = self.fika_msg
        fika_msg.conversation_id = conversation_id

        conversation, observe_timestamp = self.fworld.observe(user_request=fika_msg)
        brain_response = self.fworld.act(conversation, observe_timestamp)


    def test_message_interview(self):    
        interview_response = self.iworld.init_conversation(self.interview_init, self.build_data) 
        conversation_id = interview_response.conversation_id

        interview_msg = self.interview_msg
        interview_msg.conversation_id = conversation_id

        conversation, observe_timestamp, intent = self.iworld.observe(user_request=interview_msg)
        brain_response = self.iworld.act(conversation, observe_timestamp, intent)       


class TestNewJsonSchema(TestOldJsonSchema):
    """ Inherits methods but has a setup with new Json Schema (without password and with user_id)

    """

    @classmethod
    def setup_class(cls):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.fworld = FikaWorld()
        cls.iworld = InterviewWorld()

        fika_init = {
            "name": "Pytest",
            "created_at": '1999-04-07 18:59:24.584658',
            "persona": "fika",
            "development_testing": True,
            "webapp_local": True,
            "webapp_url": "pytest",
            "webapp_version": "NA",
            "brain_url": "NA",
            "lang": "sv",
            "user_ip_number": "127.0.0.1",
            "user_id": "123456"
            }

        interview_init = {
            "name": "Pytest",
            "job": "Pytest",
            "created_at": '1999-04-07 18:59:24.584658',
            "persona": "intervju",
            "development_testing": True,
            "webapp_local": True,
            "webapp_url": "pytest",
            "webapp_version": "NA",
            "brain_url": "NA",
            "lang": "sv",
            "user_ip_number": "127.0.0.1",
            "user_id": "123456"
            }

        fika_msg = {
            "message": "This is a test message you can change",
            "conversation_id": "__CHANGE_ME__",
            "response_time": -1,
            "created_at": "1999-04-07 18:59:24.584658",
            "recording_used": False,
            "lang": "sv",
                    }
        
        interview_msg = {
            "message": "This is a test message you can change",
            "conversation_id": "__CHANGE_ME__",
            "response_time": -1,
            "created_at": "1999-04-07 18:59:24.584658",
            "recording_used": False,
            "lang": "en",
                        }

        cls.build_data = {'brain_version': 'lol no idea it does not matter', 'brain_url': 'lol idk'}
        cls.fika_init = InitBody(**fika_init)
        cls.interview_init = InitBody(**interview_init)
        cls.fika_msg = UserMessage(**fika_msg)
        cls.interview_msg = UserMessage(**interview_msg)