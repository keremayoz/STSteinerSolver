import os
import xlrd
import csv

# Builds the terminal command with given parameters
def build_command(NETWORK_FILE, PRIZE_FILE, MSGSTEINER_BIN, CONFIG_FILE, STP_DIR, CLUSTER_DIR, LOG_DIR, CLUSTER_LIST_FILE, ART_PRIZES_DIR, BETA, LAMBD, ALPHA, EXP_ID, FOLD, PRIZE_MODE):
    command = "python ./bin/st_steiner --network_file=data/"
    command += NETWORK_FILE
    command += " --prize_file="
    command += PRIZE_FILE
    command += " --msgsteiner_bin="
    command += MSGSTEINER_BIN
    command += " --config_file="
    command += CONFIG_FILE
    '''
    command +=" --stp_dir="
    command += STP_DIR
    command += " --cluster_dir="
    command += CLUSTER_DIR
    command += " --log_dir="
    command += LOG_DIR
    '''
    command += " --cluster_list_file="
    command += CLUSTER_LIST_FILE
    '''
    command += " --art_prizes_dir="
    command += ART_PRIZES_DIR
    '''
    command += " -b="
    command += BETA
    command += " -l="
    command += LAMBD
    '''
    command += " -a="
    command += ALPHA
    '''
    command += " --exp_id="
    command += EXP_ID
    '''
    command += " --fold="
    command += FOLD
    command += " --prize_mode="
    command += PRIZE_MODE
    command += " --retain_intermediate"
    '''
    return command

# Reads the ground truth file and returns a gene list of first 108 genes
def readGroundTruthFile():
    workbook = xlrd.open_workbook("data/groundTruth.xlsx", "rb")
    sheets = workbook.sheet_names()
    required_data = []
    for sheet_name in sheets:
        sh = workbook.sheet_by_name(sheet_name)
        i = 0
        for rownum in range(sh.nrows):
            if i == 108:
                break
            if i != 0:
                row_valaues = sh.row_values(rownum)
                required_data.append((row_valaues[0]))
            i += 1
    return required_data

# Reads the cluster file with specified name and return the list of genes in that cluster
def readCluster(name):
    lis = []
    with open(name, 'r') as f:
        reader = csv.reader(f, dialect='excel', delimiter='\t')
        for row in reader:
            lis.append(row[0])
    return lis

#################################################################
#
# After that function, the first window of each network
# is solved with different beta values and lambda = 0.
# Best results of each solution and its beta value are saved.
# Beta starts from the 0 and increased specified amount.
#
##################################################################
def firstWindow(initialBeta, decreaseAmount):

    # File list
    files = ["ap1_07.wnetwork", "bp1_07.wnetwork", "ap2_07.wnetwork", "bp2_07.wnetwork", "n1_05.wnetwork", "n2_05.wnetwork", "n3_05.wnetwork"]
    files = ["n3_05.wnetwork"]
    # Fixed parameters
    prize_file = "data/tada_qval_rubeis14_iossifov14_2015_bspan_mapped.txt"
    msg_bin = "../msgsteiner-1.3/msgsteiner"
    config_file = "config/setting_1-rsqd.ini"

    # Change the working directory to ST-Steiner
    os.chdir("../ST-Steiner-env/ST-Steiner")

    # Get ground truth genes as list
    ground = readGroundTruthFile()

    # Boolean flags whether the beta selection is completed or not
    done = [False] * len(files)

    # For every network...
    for index in range(len(files)):
        prev_count = 0
        prev_length = 1
        # Exp_id is for the actual name of cluster while temp_id is the next trial. Temp_id file is deleted when the correct parameter is selected.
        exp_id = "cluster_" + files[index][:-9]
        temp_exp_id = "temp_cluster_" + files[index][:-9]

        # Add the clusters to cluster list
        os.system("echo 'clusters/" + exp_id + ".txt' >> clusters/cluster_list.txt;")


        while not done[index]:

            # Every file has its own beta, build the command with it
            command = build_command(files[index], prize_file, msg_bin, config_file, "", "", "", "None", "", str(initialBeta[index]), str(0), "", temp_exp_id, "", "")

            # Execute
            os.system(command)

            # Read cluster
            currentFile = readCluster("clusters/" + temp_exp_id + ".txt")

            # Calculate intersection count
            intersection_count = len(set(ground).intersection(set(currentFile)))

            # If it starts to decrease, stop and delete that result and obtain the previous result
            if intersection_count / len(currentFile) < prev_count / prev_length:

                # Recover
                initialBeta[index] -= decreaseAmount
                os.remove("clusters/" + temp_exp_id + ".txt")

                # End the search
                done[index] = True

            # Else continue with smaller beta to reduce the network while containing ground truth genes
            else:

                # Change beta
                initialBeta[index] += decreaseAmount

                # Delete the old worse result,
                if os.path.isfile("clusters/" + exp_id + ".txt"):
                    os.remove("clusters/" + exp_id + ".txt")

                # And rename the temporary file as the actual cluster, update the previous count
                os.rename("clusters/" + temp_exp_id + ".txt", "clusters/" + exp_id + ".txt")
                prev_count = intersection_count
                prev_length = len(currentFile)

    # Return the suitable beta values
    return initialBeta


####################################################################################
#
# After that function, the next windows are solved for networks.
# Firstly, the ap-bp networks are solved together to obtain the network
# which has the most intersection with the ground truth genes.
#
# After the best solutions of ap-bp networks, n networks are started to solve.
# The best results of n networks are found as a result and the suitable lambda
# parameters are returned as a result. In the end of that operations, all the
# networks have the best solutions. Lambda is changing while solving the networks.
#
####################################################################################
def nextWindows(initialLambdas, completeBetas, divisionAmount):

    # Fixed parameters
    prize_file = "data/tada_qval_rubeis14_iossifov14_2015_bspan_mapped.txt"
    msg_bin = "../msgsteiner-1.3/msgsteiner"
    config_file = "config/setting_1-rsqd.ini"
    cluster_list = "clusters/cluster_list.txt"

    # Change the working directory to ST-Steiner
    os.chdir("../ST-Steiner-env/ST-Steiner")
    ground = readGroundTruthFile()

    # Ap-Bp files are solved until the best results are obtained
    files = ["ap1_07.wnetwork", "bp1_07.wnetwork", "ap2_07.wnetwork", "bp2_07.wnetwork"]
    length = len(files)

    # Previous intersection is stored because the networks are solved in alternating order
    prev_intersection = [0] * length
    prev_length = [1] * length
    # Boolean flags for completion
    done = [False] * length

    # Index for accessing the correct network
    i = 0

    # Continue until all of them are completed
    while False in done:

        # Exp_id is for the actual name of cluster while temp_id is the next trial. Temp_id file is deleted when the correct parameter is selected.
        exp_id = "cluster_" + files[i % length][:-9]
        temp_exp_id = "temp_cluster_" + files[i % length][:-9]

        # Every file has its own beta, so we take modulo to differentiate the file
        command = build_command(files[i % length], prize_file, msg_bin, config_file, "", "", "", cluster_list, "", str(completeBetas[i%length]), str(initialLambdas[i % length]), "", temp_exp_id, "", "")
        os.system(command)

        # Read cluster
        currentFile = readCluster("clusters/" + temp_exp_id + ".txt")

        # Calculate intersection count, if it decreases stop.
        intersection_count = len(set(ground).intersection(set(currentFile)))

        # If it starts to decrease, stop and recover the last lambda for that file
        if intersection_count / len(currentFile) < prev_intersection[i%length] / prev_length[i%length]:

            # Recover files and parameter
            initialLambdas[i%length] *= divisionAmount
            os.remove("clusters/" + temp_exp_id + ".txt")
            done[i%length] = True

        # Else continue with smaller beta to reduce the network while containing ground truth genes
        else:

            # Change lambda
            initialLambdas[i%length] /= divisionAmount

            # Delete the old file
            if os.path.isfile("clusters/" + exp_id + ".txt"):
                os.remove("clusters/" + exp_id + ".txt")

            # Rename the cluster with better stats
            os.rename("clusters/" + temp_exp_id + ".txt", "clusters/" + exp_id + ".txt")

            # Update the previous result
            prev_intersection[i%length] = intersection_count
            prev_length[i%length] = len(currentFile)

        # Go to next file
        i += 1

    # Ap-Bp solutions are completed.


    # N files are started to solve
    files2 = ["n1_05.wnetwork", "n2_05.wnetwork", "n3_05.wnetwork"]
    length2 = len(files2)
    prev_intersection2 = [0] * length2
    prev_length2 = [1] * length2
    done2 = [False] * length2
    i = 0

    while False in done2:
        exp_id = "cluster_" + files2[i % length2][:-9]
        temp_exp_id = "temp_cluster_" + files2[i % length2][:-9]

        # N files are at the end of the list so access them by applying arithmetic operations
        command = build_command(files2[i % length2], prize_file, msg_bin, config_file, "", "", "", cluster_list, "", str(completeBetas[i % length2 + length]), str(initialLambdas[i % length2 + length]), "", temp_exp_id, "", "")
        os.system(command)

        # Read cluster
        currentFile = readCluster("clusters/" + temp_exp_id + ".txt")

        # Get the intersection
        intersection_count = len(set(ground).intersection(set(currentFile)))

        # If it starts to decrease, stop and recover the last beta for that file
        if intersection_count / len(currentFile) < prev_intersection2[i % length2] / prev_length2[i % length2]:
            initialLambdas[i%length2+length] *= divisionAmount
            os.remove("clusters/" + temp_exp_id + ".txt")
            done2[i % length2] = True

        # Else continue with smaller beta to reduce the network while containing ground truth genes
        else:
            initialLambdas[i%length2+length] /= divisionAmount
            if os.path.isfile("clusters/" + exp_id + ".txt"):
                os.remove("clusters/" + exp_id + ".txt")
            os.rename("clusters/" + temp_exp_id + ".txt", "clusters/" + exp_id + ".txt")
            prev_intersection2[i % length2] = intersection_count
            prev_length2[i%length2] = len(currentFile)
        i += 1

    # N networks are solved

    return initialLambdas

def solve(betas, lambdas, decrease, divide):

    result_beta = firstWindow(betas, decrease)
    thefile = open('betas.txt', 'w')

    for item in result_beta:
        thefile.write("%s\n" % item)

    result_lambda = nextWindows(lambdas,result_beta, divide)
    thefile2 = open('lambdas.txt', 'w')

    for item in result_lambda:
        thefile2.write("%s\n" % item)


x = 0.2
y = 0.1
betas = [0.2,0.1,0.5,0.1,0.5,0.7,100]

lambdas = [y,y,y,y,y,y,y]

solve(betas,lambdas, -0.02, 2)







































