# Command line arguments
import argparse
import sys
# Interactive menu
import cmd
import readline
# File interaction
import os
import errno

# Simulation
from SocialNetworkCore import SocialNetwork
from ADT.DSALinkedList import *


# Ben said ok
class interactive(cmd.Cmd):
    intro = "Type help or ? to list commands.\n"
    prompt = "(social-sim) "

    def __init__(self):
        super(interactive, self).__init__()
        self._network = SocialNetwork()

    def do_load(self, arg):
        'Load a social network: load <netfile>'
        try:
            with open(arg, "r") as f:
                self._network.loadNetwork(f)
        except IOError as ioex:
            print(f"File could not be read: {os.strerror(ioex.errno)}")
        except ValueError as vEx:
            print(str(vEx))

    def do_find_user(self, arg):
        'Find a user and display their posts, followers, and following: find_user <name>'
        try:
            user = self._network.findUser(arg)
            print("#posts")
            for x in user.posts:
                print(f"content: {x.content}")
                print("liked:")
                [print(y.name()) for y in x.liked()]
            print("#followers")
            [print(x.name()) for x in user.followers()]
            print("#following")
            [print(x.name()) for x in user.following()]
        except ValueError as ex:
            print(str(ex))
        
    def do_add_user(self, arg):
        'Add a user: add_user <name>'
        try:
            self._network.addUser(arg)
        except ValueError as ex:
            print(str(ex))

    def do_remove_user(self, arg):
        'Remove a user: remove_user <name>'
        try:
            self._network.removeUser(arg)
        except ValueError as ex:
            print(str(ex))

    def do_like(self, arg):
        'Like a post: like <user>'
        try:
            self._network.like(arg)
        except ValueError as ex:
            print(str(ex))

    def do_unlike(self, arg):
        "Unlike a post: unlike <user>"
        try:
            self._network.unlike(arg)
        except ValueError as ex:
            print(str(ex))

    def do_follow(self, arg):
        "Follow a user: follow <followed>:<follower>"
        args = arg.split(':')
        if len(args) == 2:
            try:
                if not self._network.follow(args[1], args[0]):
                    print(f"{args[1]} is already following {args[0]}.")
            except ValueError as ex:
                print(str(ex))
        else:
            print("Invalid usage.")

    def do_unfollow(self, arg):
        "Unfollow a user: unfollow <followed>:<follower>"
        args = arg.split(':')
        if len(args) == 2:
            try:
                self._network.unfollow(args[1], args[0])
            except ValueError as ex:
                print(str(ex))
        else:
            print("Invalid usage.")

    def do_prob(self, arg):
        'Set the probabilities of the social network: prob <prob_like> <prob_foll>'
        args = arg.split()
        if len(args) == 2:
            try:
                self._network.probLike = float(args[0])
                self._network.probFollow = float(args[1])
            except ValueError as ex:
                print(str(ex))
        else:
            print("Invalid usage.")

    def do_post(self, arg):
        'Create a new post: post <name>:<content>:<(optional) clickbaitFactor>'
        args = arg.split(':')
        try:
            if len(args) == 2:
                self._network.addPost(args[0], args[1])
            elif len(args) == 3:
                self._network.addPost(args[0], args[1], float(args[2]))
            else:
                print("Invalid usage.")
        except ValueError as ex:
            print(str(ex))

    def do_display(self, arg):
        'Display the social network: display'
        self._network.display()

    def do_stats(self, arg):
        'Display social network statistics: stats'
        print(self._network.optionalStats())

    def do_posts(self, arg):
        'Display posts in order of popularity: posts'
        [print(f"user: {x.user().name()}\ncontent: {x.content}\nlikes: {sum(1 for _ in x.liked())}\n") for x in self._network.popularPosts()]

    def do_users(self, arg):
        'Display users in order of popularity: users'
        [print(f"user: {x.name()}\nfollowers: {len(x.followers())}\n") for x in self._network.popularUsers()]

    def do_update(self, arg):
        'Run a timestep: update'
        try:
            self._network.update()
        except ValueError as vEx:
            print(str(vEx))

    def do_save(self, arg):
        'Save the network: save <filename>'
        try:
            with open(arg, "f") as f:
                f.write(self._network.save())
        except IOError as ioex:
            print(f"File could not be read: {os.strerror(ioex.errno)}")

    def do_exit(self, arg):
        'Exit the program: exit'
        return True


def simulationInterface(netfile, eventfile, prob_like, prob_foll):
    try:
        fileName, _ = simulation(netfile, eventfile, prob_like, prob_foll)
        print(f"Simulation logged to {fileName}")
    except ValueError as ex:
        print(str(ex))
        raise ex


def simulation(netfile, eventfile, prob_like, prob_foll):
    network = SocialNetwork(probLike=prob_like, probFollow=prob_foll)
    network.loadNetwork(netfile)
    events = [x.rstrip('\n') for x in eventfile]
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False, mode='w') as f:
        filename = f.name
        fileData, stats = execEventFile(network, events)
        f.write(fileData)
    return filename, stats


def execEventFile(network, eventFile) -> str:
    outcome = ""
    from collections import namedtuple
    SimStats = namedtuple('SimStats', 'post likes clustering favg fsd')
    stats = DSALinkedList()
    post = 0
    for x in eventFile:
        tokens = x.split(':')
        if len(tokens) == 3 and tokens[0] == "F":
            network.follow(tokens[2], tokens[1])
        elif len(tokens) == 3 and tokens[0] == "U":
            network.unfollow(tokens[2], tokens[1])
        elif len(tokens) == 2 and tokens[0] == "A":
            network.addUser(tokens[1])
        elif len(tokens) == 2 and tokens[0] == "R":
            network.removeUser(tokens[1])
        elif len(tokens) == 3 or len(tokens) == 4 and tokens[0] == "P":
            if len(tokens) == 3:
                network.addPost(tokens[1], tokens[2])
            else:
                network.addPost(tokens[1], tokens[2], float(tokens[3]))
            while not network.done():
                stats.insertLast(SimStats(post, network.likesScaled(),
                                           network.clusteringCoefficient(), *network.followsAvSd()))
                outcome += network.simstate()
                outcome += (f"Likes per person per post: {stats.peekFirst().likes}\n"
                            f"Follower Average: {stats.peekFirst().favg}\nFollower s.d: {stats.peekFirst().fsd}\n"
                            f"Clustering Coefficient: {stats.peekFirst().clustering}")
                network.update()
            post += 1
        else:
            raise ValueError("Invalid file format.")
    return outcome, stats


def make_parser():
    parser = argparse.ArgumentParser(description="Simulate Social Networks.",
                                     add_help=False, prefix_chars='\0')
    subparsers = parser.add_subparsers(dest="mode")

    simulation_parser = subparsers.add_parser("-s", add_help=False,
                                              help="Run in simulation mode")
    interactive_parser = subparsers.add_parser("-i", add_help=False,
                                               help="Run in interactive mode")

    simulation_parser.add_argument('netfile', type=argparse.FileType('r'),
                                   help='File that describes the initial network')
    simulation_parser.add_argument('eventfile', type=argparse.FileType('r'),
                                   help='File that lists all events on the network')
    simulation_parser.add_argument('prob_like', type=float,
                                   help='Probability of liking a post')
    simulation_parser.add_argument('prob_foll', type=float,
                                   help='Probability of following the original poster of a liked post')
    return parser, interactive_parser, simulation_parser


if __name__ == "__main__":
    parser, interactive_parser, simulation_parser = make_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        interactive_parser.print_help(sys.stderr)
        simulation_parser.print_help(sys.stderr)
    else:
        args = parser.parse_args()
        if args.mode == "-i":
            try:
                interactive().cmdloop()
            except KeyboardInterrupt:
                print("")
        elif args.mode == "-s":
            simulationInterface(args.netfile, args.eventfile, args.prob_like, args.prob_foll)
