# Function to evalaute final positions based on the movement of the dancers
def evaluate_movement(moves, pos):
    # moves store movement for each dancer
    # taking curr dancers pos as pos 1 2 3

    # dancer at pos 1 goes right
    if moves[pos[0] - 1] == "R":
        # dancer at pos 2 goes left
        if moves[pos[1] - 1] == "L":
            # dancer at pos 3 goes left
            if moves[pos[2] - 1] == 'L':
                # 2 3 1
                pos = [pos[1], pos[2], pos[0]]
            else:
                # 2 1 3
                pos = [pos[1], pos[0], pos[2]]

        # if dancer at pos 2 goes right
        elif moves[pos[1] - 1] == "R":
            # one case only
            if moves[pos[2] - 1] == "L":
                # 3 1 2
                pos = [pos[2], pos[0], pos[1]]

        # dancer at pos 2 does not move
        else:
            if moves[pos[2] - 1] == "L":
                # 3 2 1
                pos = [pos[2], pos[1], pos[0]]

    # dancer in pos 1 does not move
    else:
        # dancer in pos 2 goes right
        if moves[pos[1] - 1] == "R":
            # 1 3 2
            pos = [pos[0], pos[2], pos[1]]
    return pos

# pos = [1, 2, 3] # array index rep position, numer rep dancer

# print(f"pos: {pos}")
# moves = ['N', 'R', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 132


# moves = ['R', 'L', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 231

# moves = ['R', 'L', 'N']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 213

# moves = ['R', 'R', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 312

# moves = ['R', 'N', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 321

# pos = [1, 3, 2] # array index rep position, numer rep dancer

# pos = [1, 3, 2] # array index rep position, numer rep dancer

# print(f"pos: {pos}")
# moves = ['N', 'L', 'R']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 123

# moves = ['R', 'L', 'N']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 231

# moves = ['R', 'L', 'R']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 213

# moves = ['R', 'N', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 312

# moves = ['R', 'L', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 321

# pos = [2, 1, 3] # array index rep position, numer rep dancer

# print(f"pos: {pos}")
# moves = ['L', 'R', 'N']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 123

# moves = ['L', 'R', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 231

# moves = ['R', 'N', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 213

# moves = ['N', 'R', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 312

# moves = ['R', 'R', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 321

# pos = [2, 3, 1] # array index rep position, numer rep dancer

# print(f"pos: {pos}")
# moves = ['L', 'R', 'R']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 123

# moves = ['L', 'R', 'N']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 132

# moves = ['L', 'N', 'R']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 213

# moves = ['L', 'R', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 312

# moves = ['N', 'R', 'L']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 321

# pos = [3, 2, 1] # array index rep position, numer rep dancer

# print(f"pos: {pos}")
# moves = ['L', 'N', 'R']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 123

# moves = ['L', 'R', 'R']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 132

# moves = ['L', 'L', 'R']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 213

# moves = ['N', 'L', 'R']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 231

# moves = ['L', 'R', 'N']
# new_pos = evaluate_movement(moves, pos)
# print(f"pos: {new_pos}")
# # 312
