files = dict(
    #pathes are counted from the tournament_analyzer folder

    #path to xlsx file with history of standard format 
    #
    history = './data/sibypt.xlsx',

    #place to create files with results
    #
    output_stats = './output/sibypt_stat.dat',
    output_g_p = './output/sibypt_g_minus_p.dat'
)

#True if all grades are recorded 0..10
#False if IYNT system is used (0..30 rep, 0..20 opp, 0..10 rev)
#
is_IYPT = True

#True if history tables already contain calculated P. The script will overwrite them  
#
p_row_is_present = False

#based on functionality
#
cols_stats = ['fight', 'teams', 'N','N_order','N_winner','frac_order','frac_winner', 'W', 'rho']
cols_g_p = ['fight', 'type', 'G', 'P', 'G-P']
digits_rd = 7

#No need to change, used for debugging readability
#
team_codes = ['A','B','C','D']