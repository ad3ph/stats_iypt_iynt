import pandas
from numpy import split as n_split
from src.round import rd
from src.config import cols_g_p, p_row_is_present
from src.decorators import debug

'''Tournament stuff'''
def give_ranks(_df): 
    '''_df is a DataFrame, contains Team and SP cols, A B C D teams
    Returns DataFrame with new col "Rank" containing numerical rank 1 2 3 4 or tied,
    sum of ranks is always 1+2+3+4=10'''

    #basic ranking 1,2,3,4 from max to min
    _sorted_df = _df.sort_values('SP', ascending=False, ignore_index=True)
    _sorted_df['Rank'] = [1,2,3,4]

    #processing ties
    for a in range(3):
        _ath, _next = _sorted_df.loc[_sorted_df.index[a:a+2], 'SP'].tolist()
        duplication_happens = (_ath == _next) and (_ath != 0)
        if duplication_happens:
            divided_rank = (_sorted_df.Rank[a]+_sorted_df.Rank[a+1]) / 2
            _sorted_df.at[_sorted_df.index[a],'Rank'] = divided_rank
            _sorted_df.at[_sorted_df.index[a+1],'Rank'] = divided_rank

    return _sorted_df

def find_P(_in):
    '''_in - Series of grades
    Returns integer P calculated based on IYNT rules
    '''
    return rd((_in.sum() - _in.max() - _in.min() + ((_in.max() + _in.min())/2)) / int(len(_in)-1),7) 

def get_team_num(_in):
    '''_in - DataFrame'''
    return int((_in.iloc[0].count())/3)

def get_fight_type(_in):
    '''_in - DataFrame.
    Returns:
    [[cols for team 1],[cols for team 2],[cols for team 3],[cols for team 4]]  
    '''
    _team_num = int((_in.iloc[0].count())/3)
    if _team_num == 3:
        return [[0, 5, 7],[1, 3, 8],[2, 4, 6],[]]
    if _team_num == 4:
        return [[0, 8, 10],[1, 3, 11],[2, 4, 6],[5, 7, 9]]
    if _team_num == 2:
        return [[0, 4, 5],[1, 2, 3],[],[]]

def clean_up_fight(_df):
    '''Drops row with fight code, row with P and is_na col'''
    _df.drop(index=_df.head(1).index, inplace=True, axis=0)
    
    if p_row_is_present:
        _df.drop(index=_df.tail(1).index, inplace=True, axis=0)

    _df.drop('is_na', axis=1, inplace=True)
    _df.iloc[:, :] = _df.iloc[:, :].astype('float64')
    return _df

'''DataFrame modifiers'''
def clean_up(_df):
    '''Drop NaN rows'''
    for i in _df:
        i.drop(i[i.is_na == True].index, inplace=True)
    return _df

def split_by_empty_row(_df):
    '''__doc__ = __name__'''
    _df['is_na'] = _df[_df.columns].isnull().apply(lambda x: all(x), axis=1)
    _divLines = _df.query('is_na == True').index
    _splitted = n_split(_df, _divLines, axis=0)
    return _splitted

def head_to_g_p_table(_fight_df, _fight_code):
    '''Creates a DF which will be appended to G-P table.'''
    out_df = pandas.DataFrame(columns=cols_g_p)

    #iterating through all grades
    for b in range(_fight_df.shape[1]):
        for a in range(_fight_df.shape[0]-1):
            this_G = _fight_df.iloc[a,b]
            
            grade_type = 'Rep'
            if b in [1, 4, 7, 10]:
                grade_type = 'Opp'
            if b in [2, 5, 8, 11]:
                grade_type = 'Rev'

            if not pandas.isna(this_G):
                #find corresponding G and G-P
                this_P = rd(_fight_df.iloc[_fight_df.shape[0]-1, b], 2)
                this_G_minus_P = rd(round(this_G - this_P, 5), 2)
                row_to_df = pandas.DataFrame([[_fight_code, grade_type, this_G, this_P, this_G_minus_P]], columns=cols_g_p)
                out_df = pandas.concat([out_df, row_to_df], ignore_index=True)
    return out_df