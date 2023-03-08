import random

import time 

import sys 

sys.path.append('../') 

from Common_Libraries.p2_lib import * 
  

import os 

from Common_Libraries.repeating_timer_lib import repeating_timer 


def update_sim (): 

    try: 

        arm.ping() 

    except Exception as error_update_sim: 

        print (error_update_sim) 

  

arm = qarm()                         
update_thread = repeating_timer(2, update_sim)


#Initializing global variables

gripper_open = True
drawer_status = [False, False, False]


def main():
    '''
    Function: main()
    Purpose: Execute workflow for each randomly generated container based on step
             varible that ensures it is executed in correct order
    Author: Xiang Zhang & Marcus Cohoon
    Last Updatated: Novemeber 30, 2020
    '''
    #Author: Marcus Cohoon
    #Create a list of container ID's in random order
    containers = []
    while len(containers) < 6:
        x = random.randint(1,6)
        if x not in containers:
            containers.append(x)
    print ("")
    print ("Order of containers:", containers)

    #Author: Xiang Zhang
    for i in containers:
        step  = 0
        while True:
            #Obtain data from muscle sensor emulator
            left_data = arm.emg_left()
            right_data = arm.emg_right()

            #Check which step of the workflow the simulation is on and executes the current task accordingly
            if step == 0:
                print ("New container coming! Cotainer ID:", i)
                #Spawns cage from the generated random list
                arm.spawn_cage(i)
                print ("Move on to step 1 - move end effector")
                step += 1

            elif step == 1:
                #The variable completed holds a boolean value that is used to check if the function called executes correctly
                completed = move_end_effector(left_data, right_data, [0.528,0.0,-0.0019])
                if completed:
                    step += 1
                    print ("Move on to step 2 - control gripper")
                    completed = False

            elif step == 2:
                #Grab the container by closing gripper
                completed = open_and_close_gripper(right_data,left_data)
                if completed:
                    time.sleep(2)
                    arm.move_arm(0.4064,0.0,0.4826)
                    step += 1
                    print ("Move on to step 3 - move end effector")
                    completed = False
                    

            elif step == 3:
                #Determine the colour of the container
                colour = i % 3
                if colour == 0:
                    colour = 3
                completed = move_end_effector(left_data, right_data, autoclave_bin_location(colour,i>3))
                if completed:
                    step += 1
                    print ("Move on to step 4 - control gripper(small) / control drawer(larger)")
                    completed = False

            elif step == 4:
                #If the contianer is small(i<=3) release container
                #If it is large open the bin drawer
                if i <= 3:
                    completed = open_and_close_gripper(right_data,left_data)
                    if completed:
                        step += 1
                        print ("Move on to step 5 - move to home position")
                        completed = False
                else:
                    completed = open_close_drawer(left_data, right_data, i)
                    if completed:
                        step += 1
                        print ("Move on to step 5 - control gripper")
                        completed = False

            elif step == 5:
                #If the container is small move to home position and break out of while loop
                #if it is large release container
                if i <= 3:
                    completed = move_end_effector(0.5, 0, [0.4064,0.0,0.4826])
                    if completed:
                        print ("Move on to step 0 - a new container")
                        print ("")
                        completed = False
                        break
                else:
                    completed = open_and_close_gripper(right_data,left_data)
                    if completed:
                        step += 1
                        print ("Move on to step 6 - control drawer")
                        completed = False

            elif step == 6:
                #if container is large close the bin drawer
                completed = open_close_drawer(left_data, right_data, i)
                if completed:
                    step += 1
                    print ("Move on to step 7 - move to home position")
                    completed = False

            elif step == 7:
                #If the container is large return to home position
                completed = move_end_effector(0.5, 0, [0.4064,0.0,0.4826])
                if completed:
                    print ("Move on to step 0 - a new container")
                    print ("")
                    completed = False
                    #Break out of while loop after the workflow for a container is finished
                    break

    print ("Finished.")




def move_end_effector(left_arm_data, right_arm_data, final_location):
    ''' 
    Function: move_end_effector() 
    Purpose: This function takes in data from left arm and right arm,and decide 
             whether to move the arm to intended position 
    Input: left_arm_data and right_arm_data - data from emulator 
           final_location - the intended position for q-arm 
    Output: a boolean value that shows whether the arm is moved 
    Author: Xiang Zhang 
    Last Update: November 30, 2020 
    '''
    # move the q-arm to intended location if left arm data exceed threshold value
    # and right arm data is less than the variable, max_value
    threshold = 0.4
    max_value = 0.05
    if left_arm_data >= threshold and right_arm_data < max_value:
        time.sleep(2)
        arm.move_arm(final_location[0],final_location[1],final_location[2])
        time.sleep(2)
        return True
    else:
        return False

def autoclave_bin_location(colour, large):
    """
    Function: autoclave_bin_location()
    Purpose: Returns the location of autoclave bin based on size of the spawned container and colour of container 
    Input: colour - represented by a number between 1-3
           large - a boolean representing size of caontainer
    Output: Location of autoclave in form of a list
    Authour: Marcus Cohoon
    Last Updated: November 30, 2020
    
    """
    if large == True:
        location = [[-0.3992,0.1617,0.322],[0.0,-0.42,0.3],[0.0,0.42,0.3]]
    else:
        location = [[-0.6052,0.2452,0.3998],[0.0,-0.6573,0.3998],[0.0,0.6573,0.3998]]

    if colour == 1:  # red
        return location[0]
    elif colour == 2:   # green
        return location[1]
    elif colour == 3:   # blue
        return location[2]
    else:
        print ("Error: This colour is unknown.")
        return [0.4064,0.0,0.4826]


def open_close_drawer(left_arm_data, right_arm_data, container_ID):
    ''' 
    Function: open_close_drawer() 
    Purpose: This function takes in data from left arm and right arm, and 
             the container ID that is currently being processed. It then 
             determine whether or not to open the corresponding drawer. 
    Input: left_arm_data and right_arm_data - data from emulator 
           container_ID - a number from 1 to 6 that indicates the 
                          container now being processes 
    Output: a boolean value that determines if the task was completed
    Author: Xiang Zhang
    Last Update: November 30, 2020 
    ''' 
    global drawer_status
    # open or close the drawer if both left and right hand data exceed threshold
    threshold = 0.4
    if left_arm_data >= threshold and right_arm_data >= threshold:
        if container_ID == 4:
            if drawer_status[0]:
                time.sleep(2)
                arm.open_red_autoclave(False)
                time.sleep(2)
                # changing boolean in drawer_status to False representing a closed drawer
                drawer_status[0] = False
                return True
            else:
                time.sleep(2)
                arm.open_red_autoclave(True)
                time.sleep(2)
                # changing boolean in drawer_status to True representing a open drawer
                drawer_status[0] = True
                return True
        elif container_ID == 5:
            if drawer_status[1]:
                time.sleep(2)
                arm.open_green_autoclave(False)
                time.sleep(2)
                # changing boolean in drawer_status to False representing a closed drawer
                drawer_status[1] = False
                return True
            else:
                time.sleep(2)
                arm.open_green_autoclave(True)
                time.sleep(2)
                # changing boolean in drawer_status to True representing a open drawer
                drawer_status[1] = True
                return True
        elif container_ID == 6:
            if drawer_status[2]:
                time.sleep(2)
                arm.open_blue_autoclave(False)
                time.sleep(2)
                # changing boolean in drawer_status to False representing a closed drawer
                drawer_status[2] = False
                return True
            else:
                time.sleep(2)
                arm.open_blue_autoclave(True)
                time.sleep(2)
                # changing boolean in drawer_status to True representing a open drawer
                drawer_status[2] = True
                return True
        else:
            print ("Error: Invalid container ID")
            return False
        
def open_and_close_gripper(right_arm_data,left_arm_data):
    '''
    Function: open_and_close_gripper()
    Purpose: Opens or closes the Q-Arm gripper if the right arm exceeds the threhold while left arm is less than a small number (instead of zero to avoid glitch)
    Input: Right_arm_data - right arm data from emulator
           Left_arm_data - left arm data from emulator
    Output: a boolean varible that determines if the task was completed
    Author: Boshi Xu
    Last Updated: November 30, 2020
    '''
    global gripper_open
    # close or open the gripper if right arm data exceed threshold value
    # and left arm data is less than the variable, max_value
    threshold = 0.4
    max_value = 0.05
    if right_arm_data >= threshold and left_arm_data < max_value:
        if gripper_open == True:
            time.sleep(2)
            arm.control_gripper(55)
            time.sleep(2)
            gripper_open = False
            return True
        else:
            time.sleep(2)
            arm.control_gripper(-55)
            gripper_open = True
            return True
    else:
        return False
        
#Call main function to execute the workflow          
main()













    
