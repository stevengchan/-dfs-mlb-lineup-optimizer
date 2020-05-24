#
# Daily Fantasy Sports Major League Baseball Lineup Optimizer for Fan Duel Contests
#
# Created by Steven Chan
#

import sys, csv, argparse
from ortools.linear_solver import pywraplp

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('filename')
	parser.add_argument('-ex', nargs='*')
	parser.add_argument('-inc', nargs='*')
	args = parser.parse_args()
	if args.ex:
		excluded = set(args.ex)
	else:
		excluded = set()

	if args.inc:
		included = set(args.inc)
	else:
		included = set()
	players = {'P': [], 'C': [], '1B': [], '2B': [], '3B': [], 'SS': [], 'OF': []}
	included_players = {'P': 0, 'C': 0, '1B': 0, '2B': 0, '3B': 0, 'SS': 0, 'OF': 0}

	with open(args.filename) as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row['Nickname'] in excluded:
				continue
			if row['Position'] == 'P' and row['Probable Pitcher'] != 'Yes':
				continue
			if row['Nickname'] in included:
				player_included = 1
				included_players[row['Position']] += 1
				if row['Position'] == 'OF':
					if included_players['OF'] > 3:
						print('Cannot include more than 3 OF')
						return
				else:
					if included_players[row['Position']] > 1:
						print('Cannot include more than 1 %s' % row['Position'])
						return
			else:
				player_included = 0
			players[row['Position']].append([row['Nickname'], float(row['FPPG']), int(row['Salary']), row['Game'], row['Team'], row['Injury Indicator'], player_included])

	# Instantiate a mixed-integer solver
	solver = pywraplp.Solver('LineupSolver', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

	rangeP = range(len(players['P']))
	rangeC = range(len(players['C']))
	range1B = range(len(players['1B']))
	range2B = range(len(players['2B']))
	range3B = range(len(players['3B']))
	rangeSS = range(len(players['SS']))
	rangeOF = range(len(players['OF']))

	# Instantiate boolean variables for each player to be picked or not picked
	pickP = [solver.IntVar(0, 1, 'pickP%d' % i) for i in rangeP]
	pickC = [solver.IntVar(0, 1, 'pickC%d' % i) for i in rangeC]
	pick1B = [solver.IntVar(0, 1, 'pick1B%d' % i) for i in range1B]
	pick2B = [solver.IntVar(0, 1, 'pick2B%d' % i) for i in range2B]
	pick3B = [solver.IntVar(0, 1, 'pick3B%d' % i) for i in range3B]
	pickSS = [solver.IntVar(0, 1, 'pickSS%d' % i) for i in rangeSS]
	pickOF = [solver.IntVar(0, 1, 'pickOF%d' % i) for i in rangeOF]

	# Add constraints for 1 pick of each position, except for OF which has 3 picks
	solver.Add(solver.Sum([pickP[i] for i in rangeP]) == 1)
	solver.Add(solver.Sum([pickC[i] for i in rangeC]) == 1)
	solver.Add(solver.Sum([pick1B[i] for i in range1B]) == 1)
	solver.Add(solver.Sum([pick2B[i] for i in range2B]) == 1)
	solver.Add(solver.Sum([pick3B[i] for i in range3B]) == 1)
	solver.Add(solver.Sum([pickSS[i] for i in rangeSS]) == 1)
	solver.Add(solver.Sum([pickOF[i] for i in rangeOF]) == 3)

	# Add constraints for user given included players to must be picked in lineup
	solver.Add(solver.Sum([pickP[i] * players['P'][i][6] for i in rangeP]) == included_players['P'])
	solver.Add(solver.Sum([pickC[i] * players['C'][i][6] for i in rangeC]) == included_players['C'])
	solver.Add(solver.Sum([pick1B[i] * players['1B'][i][6] for i in range1B]) == included_players['1B'])
	solver.Add(solver.Sum([pick2B[i] * players['2B'][i][6] for i in range2B]) == included_players['2B'])
	solver.Add(solver.Sum([pick3B[i] * players['3B'][i][6] for i in range3B]) == included_players['3B'])
	solver.Add(solver.Sum([pickSS[i] * players['SS'][i][6] for i in rangeSS]) == included_players['SS'])
	solver.Add(solver.Sum([pickOF[i] * players['OF'][i][6] for i in rangeOF]) == included_players['OF'])

	# Instantiate variables for salaries of picked players at each position
	salaryP = solver.Sum([pickP[i] * players['P'][i][2] for i in rangeP])
	salaryC = solver.Sum([pickC[i] * players['C'][i][2] for i in rangeC])
	salary1B = solver.Sum([pick1B[i] * players['1B'][i][2] for i in range1B])
	salary2B = solver.Sum([pick2B[i] * players['2B'][i][2] for i in range2B])
	salary3B = solver.Sum([pick3B[i] * players['3B'][i][2] for i in range3B])
	salarySS = solver.Sum([pickSS[i] * players['SS'][i][2] for i in rangeSS])
	salaryOF = solver.Sum([pickOF[i] * players['OF'][i][2] for i in rangeOF])

	# Add constraint that the total salaries of picked players are less than or equal to salary cap
	solver.Add(salaryP + salaryC + salary1B + salary2B + salary3B + salarySS + salaryOF <= 35000)

	teams = {'BAL': 0, 'BOS': 0, 'NYY': 0, 'TAM': 0, 'TOR': 0, 'CWS': 0, 'CLE': 0, 'DET': 0, 'KAN': 0, 'MIN': 0, 'HOU': 0, 'LAA': 0, 'OAK': 0, 'SEA': 0, 'TEX': 0, 'ATL': 0, 'MIA': 0, 'NYM': 0, 'PHI': 0, 'WAS': 0, 'CHC': 0, 'CIN': 0, 'MIL': 0, 'PIT': 0, 'STL': 0, 'ARI': 0, 'COL': 0, 'LOS': 0, 'SDP': 0, 'SFG': 0}

	# Add constraints for no more than 4 picked players from the same team
	for team in teams:
		teams[team] += solver.Sum([pickP[i] * (players['P'][i][4] == team) for i in rangeP])
		teams[team] += solver.Sum([pickC[i] * (players['C'][i][4] == team) for i in rangeC])
		teams[team] += solver.Sum([pick1B[i] * (players['1B'][i][4] == team) for i in range1B])
		teams[team] += solver.Sum([pick2B[i] * (players['2B'][i][4] == team) for i in range2B])
		teams[team] += solver.Sum([pick3B[i] * (players['3B'][i][4] == team) for i in range3B])
		teams[team] += solver.Sum([pickSS[i] * (players['SS'][i][4] == team) for i in rangeSS])
		teams[team] += solver.Sum([pickOF[i] * (players['OF'][i][4] == team) for i in rangeOF])
		solver.Add(teams[team] <= 4)

	# Instantiate variables for projected points of picked players at each position
	pointsP = solver.Sum([pickP[i] * players['P'][i][1] for i in rangeP])
	pointsC = solver.Sum([pickC[i] * players['C'][i][1] for i in rangeC])
	points1B = solver.Sum([pick1B[i] * players['1B'][i][1] for i in range1B])
	points2B = solver.Sum([pick2B[i] * players['2B'][i][1] for i in range2B])
	points3B = solver.Sum([pick3B[i] * players['3B'][i][1] for i in range3B])
	pointsSS = solver.Sum([pickSS[i] * players['SS'][i][1] for i in rangeSS])
	pointsOF = solver.Sum([pickOF[i] * players['OF'][i][1] for i in rangeOF])

	solver.Maximize(pointsP + pointsC + points1B + points2B + points3B + pointsSS + pointsOF)

	result_status = solver.Solve()
	if not pywraplp.Solver.OPTIMAL:
		print('No optimal lineup possible')
	assert result_status == pywraplp.Solver.OPTIMAL
	assert solver.VerifySolution(1e-7, True)

	print('Pos | Player | Team | Game | Salary | Projected Points | Points/$ | Injury')
	total_salary = 0

	for i in rangeP:
		if pickP[i].SolutionValue():
			print('P  | %s | %s | %s | $%d | %.2f | %.2f | %s' % (players['P'][i][0], players['P'][i][4], players['P'][i][3], players['P'][i][2], players['P'][i][1], players['P'][i][1] / (players['P'][i][2] / 1000), players['P'][i][5]))
			total_salary += players['P'][i][2]

	for i in rangeC:
		if pickC[i].SolutionValue():
			print('C  | %s | %s | %s | $%d | %.2f | %.2f | %s' % (players['C'][i][0], players['C'][i][4], players['C'][i][3], players['C'][i][2], players['C'][i][1], players['C'][i][1] / (players['C'][i][2] / 1000), players['C'][i][5]))
			total_salary += players['C'][i][2]

	for i in range1B:
		if pick1B[i].SolutionValue():
			print('1B | %s | %s | %s | $%d | %.2f | %.2f | %s' % (players['1B'][i][0], players['1B'][i][4], players['1B'][i][3], players['1B'][i][2], players['1B'][i][1], players['1B'][i][1] / (players['1B'][i][2] / 1000), players['1B'][i][5]))
			total_salary += players['1B'][i][2]

	for i in range2B:
		if pick2B[i].SolutionValue():
			print('2B | %s | %s | %s | $%d | %.2f | %.2f | %s' % (players['2B'][i][0], players['2B'][i][4], players['2B'][i][3], players['2B'][i][2], players['2B'][i][1], players['2B'][i][1] / (players['2B'][i][2] / 1000), players['2B'][i][5]))
			total_salary += players['2B'][i][2]

	for i in range3B:
		if pick3B[i].SolutionValue():
			print('3B | %s | %s | %s | $%d | %.2f | %.2f | %s' % (players['3B'][i][0], players['3B'][i][4], players['3B'][i][3], players['3B'][i][2], players['3B'][i][1], players['3B'][i][1] / (players['3B'][i][2] / 1000), players['3B'][i][5]))
			total_salary += players['3B'][i][2]

	for i in rangeSS:
		if pickSS[i].SolutionValue():
			print('SS | %s | %s | %s | $%d | %.2f | %.2f | %s' % (players['SS'][i][0], players['SS'][i][4], players['SS'][i][3], players['SS'][i][2], players['SS'][i][1], players['SS'][i][1] / (players['SS'][i][2] / 1000), players['SS'][i][5]))
			total_salary += players['SS'][i][2]

	for i in rangeOF:
		if pickOF[i].SolutionValue():
			print('OF | %s | %s | %s | $%d | %.2f | %.2f | %s' % (players['OF'][i][0], players['OF'][i][4], players['OF'][i][3], players['OF'][i][2], players['OF'][i][1], players['OF'][i][1] / (players['OF'][i][2] / 1000), players['OF'][i][5]))
			total_salary += players['OF'][i][2]

	print('\nProjected Total Points: %.2f | Total Salary: $%d' % (solver.Objective().Value(), total_salary))

if __name__ == "__main__":
	main()
