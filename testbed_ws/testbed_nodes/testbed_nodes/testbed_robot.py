#!/usr/bin/env python3
from sys import stdout
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from os.path import join, expanduser
from collections import defaultdict
from time import perf_counter, sleep
import random
from fcntl import flock, LOCK_EX, LOCK_UN
import rclpy
from rclpy.node import Node
from testbed_msg.msg import TestbedMessage
from testbed_nodes.setup_reader import read_setup, qos_profile

class TestbedRobot(Node):

    def _make_publisher_timer_callback_function(self, topic_name, size,
                                                recipients, f):
        def fn():
            self.publish_counters[topic_name] += 1
            transmit_count = self.publish_counters[topic_name]

            # compose message
            msg = TestbedMessage()
            msg.publisher_name = self.robot_name
            msg.tx_count = transmit_count
            msg.message = topic_name[0]*size

            # compose network metadata log
            s = ""
            for recipient_robot_name in recipients:
                s += "%s,%s,%s,%d,%f\n"%(
                           self.robot_name,
                           recipient_robot_name,
                           topic_name,
                           transmit_count,
                           perf_counter())

            # publish the message
            self.publisher_managers[topic_name].publish(msg)

            # log the publish metadata
            flock(f, LOCK_EX) # exclusive lock
            f.write(s)
            f.flush()
            flock(f, LOCK_UN) # unlock
        return fn

    def _make_subscriber_callback_function(self, topic_name, f):
        def fn(msg):
            self.subscribe_counters[topic_name] += 1
            receive_count = self.subscribe_counters[topic_name]

            # rx log: from, to, topic, tx count, rx count, msg size, ts
            response = "%s,%s,%s,%d,%d,%d,%f\n"%(
                           msg.publisher_name,
                           self.robot_name,
                           topic_name,
                           msg.tx_count,
                           self.subscribe_counters[topic_name],
                           len(msg.message),
                           perf_counter())

            # log the response metadata
            flock(f, LOCK_EX) # exclusive lock
            f.write(response)
            f.flush()
            flock(f, LOCK_UN) # unlock
        return fn

    def __init__(self, robot_name, role, setup_file, f):
        super().__init__(robot_name)
        self.robot_name = robot_name
        self.role = role
        self.f = f

        # stagger start time randomly but deterministically
        random.seed(robot_name)
        random.random()

        # get setup parameters
        setup = read_setup(setup_file)
        publishers = setup["publishers"]
        subscribers = setup["subscribers"]
        all_recipients = setup["all_recipients"]

        # start publishers for this role
        self.publish_counters = defaultdict(int)
        self.subscribe_counters = defaultdict(int)
        self.publisher_managers = dict()
        self.publisher_timers = list()
        for publisher in publishers:
            # only publish topics assigned to this role
            if publisher["role"] != role:
                continue

            # the topic
            topic = publisher["topic"]

            # make and keep static references to publisher managers
            self.publisher_managers[topic] = self.create_publisher(
                             TestbedMessage, topic,
                             qos_profile=qos_profile(publisher))

            # recipients
            recipients = all_recipients[topic]

            # the callback function that is dynamically created using closure
            publisher_timer_callback_function = \
                            self._make_publisher_timer_callback_function(
                            topic, publisher["size"], recipients, f)
            period = 1/publisher["frequency"]
            timer = self.create_timer(period, publisher_timer_callback_function)
            self.publisher_timers.append(timer)

        # start subscribers
        self.subscriber_managers = list()
        for subscriber in subscribers:

            # only subscribe to topics assigned to this role
            if subscriber["role"] != role:
                continue

            _subscriber_callback_function = \
                            self._make_subscriber_callback_function(
                                  subscriber["topic"], f)

            subscriber_object = self.create_subscription(
                                  TestbedMessage,
                                  subscriber["topic"],
                                  _subscriber_callback_function,
                                  qos_profile=qos_profile(subscriber))
            self.subscriber_managers.append(subscriber_object)

def main():
    parser = ArgumentParser(description="Generic testbed robot.",
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("robot_name", type=str,
                        help="The name of this robot node.")
    parser.add_argument("role", type=str, help="This robot's role")
    parser.add_argument("setup_file", type=str, help="The scenario setup file.")
    parser.add_argument("out_file", type=str, help="The output file.")
    args = parser.parse_args()
    print("Starting testbed_robot %s role %s"%(args.robot_name, args.role))
    stdout.flush()

    # open out_file w+
    with open(args.out_file, "a") as f:
        rclpy.init()
        robot_node = TestbedRobot(args.robot_name, args.role,
                                  args.setup_file, f)
        rclpy.spin(robot_node)
        robot_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

