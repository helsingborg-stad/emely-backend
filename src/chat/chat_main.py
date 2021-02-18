from worlds import InterviewWorld, ChatWorld


if __name__ == '__main__':
    name = 'Alex'
    job = 'receptionist'
    mname = 'facebook/blenderbot-400M-distill' # facebook/blenderbot-1B-distill
    world = InterviewWorld(job, name, mname)

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