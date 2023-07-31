from math import sqrt
from copy import deepcopy

import pandas

from src.config import team_codes, digits_rd
from src.round import rd


def get_kendalls_w(_juror_dfs, k):
    ''' k - judges_number of teams, 
        m - judges_number of jurors,
        T_val - special value for handling ties
        team_sum_ranks - team's summary rank from all jurors
        https://www.real-statistics.com/reliability/interrater-reliability/kendalls-w/

        _juror_dfs - list of dataframes containing each juror's ranking of teams
        
        Returns W
        '''
    
    _j_tables = [_df.sort_values('Team', ignore_index=True) for _df in _juror_dfs]

    #checking for ties
    ts = []
    for _j_table in _j_tables:
        tj = [_j_table.Rank[_j_table.Rank == r].count() for r in set(_j_table.Rank.tolist()) if _j_table.Rank[_j_table.Rank == r].count() > 1]
        ts.append(tj)
    T_val = 0
    for tj in ts:
        for tg in tj:
            T_val += tg**3 - tg

    #calculating
    team_sum_ranks=[]
    m = len(_juror_dfs)

    #Summary rank of the team from all jurors is Ri 
    for _team_code in team_codes[0:k]:
        i = team_codes.index(_team_code)
        team_i_rank = sum([x.Rank[i] for x in _j_tables])
        team_sum_ranks.append(team_i_rank)
        
    s_square = sum([x**2 for x in team_sum_ranks])
    W = rd( (12*s_square - 3 * k * m**2 * (k+1)**2)/(m**2 * (k**3 - k) - m*T_val) , digits_rd)
    return W

def get_rho_sp(fight_df):
    '''
    _fight_df is a DataFrame of a fight in standard format. Without fight code and empty rows
    Returns rho_sp
    '''
    #Indices of cols always containing report grades
    reps = [0, 3, 6, 9]
    _fight_df = deepcopy(fight_df)

    p_row = _fight_df.tail(1).squeeze()
    _fight_df.drop(_fight_df.tail(1).index,inplace=True)
    _fight_df.dropna(axis='columns', inplace=True)

    judges_num = _fight_df.shape[0]

    sigma2s = []

    for i in range(3):
        #i=0 - reps, i=1 - opps, i=2 - revs
        cols_this_type = [x+i for x in reps if x+1<_fight_df.shape[1]]
        
        sigma2s.append(0)
        grade_count = 0
        
        for col in _fight_df.iloc[ : , cols_this_type]:
            grades_this_col = _fight_df[col].squeeze()

            #Replacing extreme grades in this col with their average
            half = rd((grades_this_col.max() + grades_this_col.min())/2, digits_rd)

            grades_this_col.drop([grades_this_col.idxmax(), grades_this_col.idxmin()], inplace=True)
            grades_this_col = grades_this_col.append(pandas.Series([half]),ignore_index=True)

            for grade in grades_this_col:
                sigma2s[i] += rd((p_row[col] - grade)**2, digits_rd)
                grade_count += 1
                
    sigma2s = [rd(s / grade_count, digits_rd) for s in sigma2s] #REP, OPP, REV

    sigma2_sp = rd(sum(sigma2s), digits_rd)

    rho = rd(sqrt(sigma2_sp / (judges_num - 1)), digits_rd)
    return rho