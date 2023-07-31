'''
Artem Golomolzin, Siberia
t.me/ad3ph, bently0709@gmail.com
November 2022
'''

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from datetime import datetime
import time
import copy

from humanfriendly import format_timespan
from colorama import Fore, Style
import numpy
from math import sqrt
import pandas
from progress.bar import IncrementalBar

from src.decorators import debug, welcome
import src.config as config
from src.config import team_codes, cols_stats, cols_g_p, digits_rd
from src.round import rd
from src.handlers import *
from src.calculators import *

grades_history_file = config.files['history']
out_file_stats = config.files['output_stats']
out_file_g_p = config.files['output_g_p']
 
@welcome
def main():
    #Receiving data
    print('Input file: ', end='')
    print(Fore.GREEN + grades_history_file)
    print(Style.RESET_ALL, end='')
    df = pandas.read_excel(grades_history_file)
    print('Data has been received')

    #Preprocessing data
    splitted_df = clean_up(split_by_empty_row(df))
    print('Cleanup completed')
    
    #DFs for results initialization
    print('Generating output DataFrames... ', end='')
    out_df_g_p = pandas.DataFrame(columns=cols_g_p) 
    out_df_stats = pandas.DataFrame(columns=cols_stats)
    print('completed')
    
    #Counters initialization
    fight_count = 0
    progress_bar = IncrementalBar('Processing data', max = len(splitted_df))
    t0 = datetime.now()

    # '''Iterating through fights'''

    for this_fight in splitted_df:
        '''Sample of this_fight:
                Unnamed: 0  Unnamed: 1  Unnamed: 2  Unnamed: 3  Unnamed: 4  Unnamed: 5  Unnamed: 6  Unnamed: 7  Unnamed: 8  Unnamed: 9  Unnamed: 10  Unnamed: 11  is_na
        0    1990-1-A         NaN         NaN         NaN         NaN         NaN         NaN         NaN         NaN         NaN          NaN          NaN  False      
        1           4         7.0         7.0         6.0         7.0         7.0         6.0         7.0         9.0         NaN          NaN          NaN  False      
        2           4         7.0         9.0         7.0         9.0         7.0         7.0         7.0         9.0         NaN          NaN          NaN  False      
        3           6         7.0         9.0         7.0         9.0         7.0         7.0         7.0         9.0         NaN          NaN          NaN  False      
        4           4         4.0         9.0         6.0         6.0         7.0         7.0         7.0         9.0         NaN          NaN          NaN  False      
        5           4         6.0         9.0         4.0         7.0         7.0         6.0         7.0         9.0         NaN          NaN          NaN  False      
        6           4         6.0         9.0         7.0         9.0         7.0         7.0         9.0         9.0         NaN          NaN          NaN  False      
        7           4         7.0         9.0         7.0         9.0         9.0         7.0         6.0         7.0         NaN          NaN          NaN  False      
        8           4         7.0        10.0         7.0         9.0         6.0         6.0         6.0        10.0         NaN          NaN          NaN  False      
        9           4         7.0         9.0         7.0         9.0         6.0         9.0         7.0         7.0         NaN          NaN          NaN  False      
        10          6         7.0        10.0         7.0         9.0         9.0         9.0         7.0         7.0         NaN          NaN          NaN  False      
        11          6         7.0        10.0         7.0         9.0         9.0         7.0         9.0        10.0         NaN          NaN          NaN  False      
        12        3.6         4.4         5.1         4.4         4.9         4.6         4.4         4.5         4.9         NaN          NaN          NaN  False
        '''

        if this_fight.empty:
            continue

        #Local variables and info initialization
        frac_order = 0
        frac_winner = 0
        num_NOrder = 0
        num_NWinner = 0
        num_SPs = [0,0,0,0]

        this_fight_code = this_fight.iloc[0][0]

        this_fight = clean_up_fight(this_fight)        #Cleaning up, leaving only grades
        num_N = len(this_fight.iloc[:, 1])      #Number of jurors
        row_P = pandas.Series(index=this_fight.columns, dtype='float64') # Creating row to store P
        teams_cols = get_fight_type(this_fight)
        teams_num = get_team_num(this_fight)
                
        #Converting all grades to IYNT system
        if config.is_IYPT:
            col_list = [0,3,6,9]
            for i in range(2):
                this_fight.iloc[:, [col + i for col in col_list]] *= (3-i)
        
        #Calculating P, storing it to row_P as last row of this fight
        for this_col_name in this_fight:
            this_col = this_fight[this_col_name]
            if this_col.count() != 0:
                this_col = this_col.astype(int)
                row_P[this_col_name] = find_P(this_col)
        this_fight = this_fight.append(row_P, ignore_index=True)
        this_fight_copy = copy.deepcopy(this_fight)    #Need to save it for g-p table

        #Getting numerics

        ###rho 
        num_rho = get_rho_sp(this_fight)

        ###SP for teams
        for i in range(4):
            num_SPs[i] += rd(this_fight.iloc[-1, teams_cols[i]].sum(), 2)
        team_SPs_df = pandas.DataFrame({'Team': team_codes,
                                    'SP': num_SPs})
        team_SPs_df = give_ranks(team_SPs_df)

        with open('log.txt', 'a') as log:
            log.write(f'{this_fight_code}\n{str(team_SPs_df)}\n')      

        ###Jurors' own SPs and ranks
        jurors_SPs_dfs = []
        for j in range(num_N):
            num_SPs_juror = [0,0,0,0]
            for i in range(4):
                num_SPs_juror[i] += rd(this_fight.iloc[j, teams_cols[i]].sum(), digits_rd)
            juror_SPs_df = pandas.DataFrame({'Team': ['A','B','C','D'],
                                        'SP': num_SPs_juror})
            jurors_SPs_dfs.append(give_ranks(juror_SPs_df))    
   
        
        ###Kendall's W
        num_W = get_kendalls_w(jurors_SPs_dfs, teams_num)
        
        ###N_winner and N_order
        for j in range(num_N):
            juror_df = jurors_SPs_dfs[j]
            juror_is_agree_order = (juror_df.Team.tolist() == team_SPs_df.Team.tolist()) and (juror_df.Rank.tolist() == team_SPs_df.Rank.tolist())
            juror_is_agree_winner = (juror_df.head(1).Team.tolist() == team_SPs_df.head(1).Team.tolist()) and (juror_df.head(1).Rank.tolist() == team_SPs_df.head(1).Rank.tolist())
            num_NWinner += int(juror_is_agree_winner)
            num_NOrder += int(juror_is_agree_order)
        ###Corresponding fractions
        frac_order = rd(num_NOrder / num_N, digits_rd)
        frac_winner = rd(num_NWinner / num_N, digits_rd)
        
        #Saving data
        local_data = pandas.DataFrame([[this_fight_code, teams_num, num_N, num_NOrder, num_NWinner, frac_order, frac_winner, num_W, num_rho]], columns=cols_stats)
        out_df_stats = pandas.concat([out_df_stats, local_data], ignore_index=True)
        out_df_g_p = pandas.concat([out_df_g_p, head_to_g_p_table(this_fight_copy, this_fight_code)], ignore_index=True)

        #Step for counters
        fight_count += 1
        progress_bar.next()
    
    progress_bar.finish()
    t1 = datetime.now()
    time_spent = format_timespan(t1-t0)
    print(f'Processed {fight_count} fights successfully in {time_spent}:', fight_count == len(splitted_df))

    try:
        out_df_stats.to_csv(out_file_stats, sep='\t',index=False)
        out_df_g_p.to_csv(out_file_g_p, sep='\t',index=False)
        print(Fore.GREEN + out_file_stats, end='')
        print(Fore.BLACK + ' and ', end='')
        print(Fore.GREEN + out_file_g_p, end='')
        print(Fore.BLACK + ' files created')

    except OSError:
        print(Fore.RED + 'Error saving files: directory not found. You have to manually create folder for output')

if __name__ == "__main__":
    main()