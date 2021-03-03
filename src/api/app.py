from fastapi import FastAPI
from src.chat.worlds import InterviewWorld, ChatWorld
from argparse import ArgumentParser, Namespace


def main(**kwargs):
    app = FastAPI()


    if kwargs['chat_mode'].lower() == 'interview':
        world = InterviewWorld(**kwargs)
    elif kwargs['chat_mode'].lower() == 'chat':
        world = ChatWorld(**kwargs)
    else:
        raise ValueError()

    # Print config
    print('Starting interaction with world using configuration: \n')
    for key in kwargs.keys():
        print('{}: {}\n'.format(key, kwargs[key]))

    while not world.episode_done:
        user_input = input("\tDitt svar: ")
        if not user_input:
            print('\nDu måste skriva något för att jag ska svara!')
            continue
        elif user_input == 'reset':
            print('Conversation reset\n')
            world.save()
            world.reset_conversation()
        elif user_input == 'save':
            print('Conversation saved\n')
            world.save()
        else:
            world.chat(user_input)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--name',
                        type=str, default='Alex, ',
                        help='name of user')
    parser.add_argument('--job',
                        type=str, default='programmerare',
                        help='job user is applying for in interview')
    parser.add_argument('--model_name',
                        type=str, default='blenderbot-400M-distill',
                        help='name of model')
    parser.add_argument('--local_model',
                        action='store_true', dest='local_model',
                        help='Loads model from local file in freja/models/')
    parser.add_argument('--huggingface_model',
                        action='store_false', dest='local_model',
                        help='Loads model from huggingface remote. Requires internet connection')
    parser.add_argument('--chat_mode',
                        type=str, choices=['interview', 'chat'], default='interview',
                        help='Chat mode to use. interview or open chat available')
    parser.set_defaults(local_model=True)
    args = Namespace(local_model = True, name='Alex', job='hkjsadjk', model_name ='blenderbot_small-90M')
    main(**vars(args))

