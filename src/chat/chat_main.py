from worlds import InterviewWorld, FikaWorld
from argparse import ArgumentParser
from src.api.bodys import *
from datetime import datetime
import subprocess


def main(**kwargs):
    if kwargs['chat_mode'].lower() == 'interview':
        world = InterviewWorld(**kwargs)
    elif kwargs['chat_mode'].lower() == 'chat':
        world = FikaWorld(**kwargs)
    else:
        raise ValueError()

    world.load_model()

    # Print config
    print('Starting interaction with world using configuration: \n')
    for key in kwargs.keys():
        print('{}: {}'.format(key, kwargs[key]))

    # Initing the conversation
    git_build = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode('utf-8')
    git_version = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"]).strip().decode('utf-8')
    init_body = InitBody(name=kwargs['name'],
                         job=kwargs['job'],
                         created_at=str(datetime.now()),
                         persona='intervju',
                         development_testing=True,
                         webapp_local=True,
                         webapp_url='None',
                         webapp_version='None',
                         webapp_git_build='None',
                         brain_url='None',
                         lang='sv',
                         password='KYgZfDG6P34H56WJM996CKKcNG4',
                         user_ip_number='None')
    build_data = {'brain_git_build': git_build, 'brain_version': git_version, 'brain_url': 'None'}
    episode_done = False
    brain_message = world.init_conversation(init_body=init_body, build_data=build_data)
    conversation_id = brain_message.conversation_id

    while not episode_done:
        user_input = input("\tDitt svar: ")
        user_message = UserMessage(conversation_id=conversation_id,
                                   response_time=-1,
                                   lang='sv',
                                   message=user_input,
                                   created_at=str(datetime.now()),
                                   recording_used=False,
                                   password='KYgZfDG6P34H56WJM996CKKcNG4')

        if not user_message:
            print('\nDu måste skriva något för att jag ska svara!')
            continue
        else:
            conversation, timstamp = world.observe(user_message)

            brain_response = world.act(conversation, observe_timestamp=timstamp)
            print(brain_response.message)
            episode_done = conversation.episode_done


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--name',
                        type=str, default='Alex, ',
                        help='name of user')
    parser.add_argument('--job',
                        type=str, default='programmerare',
                        help='job user is applying for in interview')
    parser.add_argument('--model_name',
                        type=str, default='blenderbot_small-90M',
                        help='name of model')
    parser.add_argument('--chat_mode',
                        type=str, choices=['interview', 'chat'], default='interview',
                        help='Chat mode to use. interview or open chat available')
    parser.add_argument('--no_correction', action='store_true', dest='no_correction')
    parser.set_defaults(local_model=True,
                        no_correction=False)
    args = parser.parse_args()
    main(**vars(args))
