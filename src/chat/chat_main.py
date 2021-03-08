from worlds import InterviewWorld, ChatWorld
from argparse import ArgumentParser


def main(**kwargs):
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

    # Initing the conversation
    conversation_id = 123456
    first_message = world.init_conversation(conversation_id, kwargs['name'], kwargs['job'])
    print(first_message)
    episode_done = False

    while not episode_done:
        user_message = input("\tDitt svar: ")
        if not user_message:
            print('\nDu måste skriva något för att jag ska svara!')
            continue
        elif user_message == 'reset':
            print('Conversation reset\n')
            world.reset_conversation(conversation_id)
        else:
            episode_done = world.observe(user_message, conversation_id)
            reply = world.act(conversation_id)
            print(reply)


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
    args = parser.parse_args()
    main(**vars(args))
