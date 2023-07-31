import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import time

import numpy
from math import sqrt
import pandas
from progress.bar import IncrementalBar

from src.decorators import debug, welcome
import src.config as config

gradesHistoryFile = config.files['history']
outFile = config.files['output_stats']
outFileGminusP = config.files['output_g_p']

colSet = ['fight', 'teams', 'N','N_order','N_winner','frac_order','frac_winner', 'W', 'rho']
colSetGminusP = ['fight', 'G', 'P', 'G-P']
teamCodes = ['A','B','C','D']

def rd(x,y=0):
    ''' A classical mathematical rounding by Voznica '''
    m = int('1'+'0'*y) # multiplier - how many positions to the right
    q = x*m # shift to the right by multiplier
    c = int(q) # new number
    i = int( (q-c)*10 ) # indicator number on the right
    if i >= 5:
        c += 1
    return c/m

def cleanUp(inData):
    for i in inData:
        i.drop(i[i.is_na == True].index, inplace=True)
    return inData

def splitByEmptyRow(inData):
    inData['is_na'] = inData[inData.columns].isnull().apply(lambda x: all(x), axis=1)
    divLines = inData.query('is_na == True').index
    splitted = numpy.split(inData, divLines, axis=0)
    return splitted

def getTeamNum(inDF):
    return int((inDF.iloc[0].count())/3)

def getFightType(inDF):
    #returns [[cols for team 1],[cols for team 2],[cols for team 3],[cols for team 4]]
    teamNum = int((inDF.iloc[0].count())/3)
    if teamNum == 3:
        return [[0, 5, 7],[1, 3, 8],[2, 4, 6],[]]
    if teamNum == 4:
        return [[0, 8, 10],[1, 3, 11],[2, 4, 6],[5, 7, 9]]
    if teamNum == 2:
        return [[0, 4, 5],[1, 2, 3],[],[]]
    
def findP(inSeries):
    funP = rd((inSeries.sum() - inSeries.max() - inSeries.min() + ((inSeries.max() + inSeries.min())/2)) / int(len(inSeries)-1),1)
    return funP

def giveRanks(inDF): 
    #contains Team and SP cols, A B C D teams
    sDF = inDF.sort_values('SP', ascending=False, ignore_index=True)
    sDF['Rank'] = [1,2,3,4]
    for a in range(3):
        ath=sDF.loc[sDF.index[a], 'SP']
        aath=sDF.loc[sDF.index[a+1], 'SP']
        duplYes = (ath==aath) and (ath != 0)
        if duplYes:
            commRank = (sDF.Rank[a]+sDF.Rank[a+1])/2
            sDF.at[sDF.index[a],'Rank'] = commRank
            sDF.at[sDF.index[a+1],'Rank'] = commRank
    return sDF
    
def giveRanksOld(inDF): 
    #contains Team and SP cols, A B C D teams
    sDF = inDF.sort_values('SP', ascending=False, ignore_index=True)
    sDF['Rank'] = [1,2,3,4]
    return sDF
 
def cleanUpFight(fightDF):
    fightDF.drop(index=fightDF.head(1).index, inplace=True, axis=0)
    fightDF.drop(index=fightDF.tail(1).index, inplace=True, axis=0)
    fightDF.drop('is_na', axis=1, inplace=True)
    fightDF.iloc[:,0] = fightDF.iloc[:,0].astype('float64')
    return fightDF
 
def headToGMinusPTable(fightDF, fightCode):
    outDF = pandas.DataFrame(columns=colSetGminusP)
    for b in range(fightDF.shape[1]):
        for a in range(fightDF.shape[0]-1):
            thisG = fightDF.iloc[a,b]
            if not pandas.isna(thisG):
                thisP = fightDF.iloc[fightDF.shape[0]-1,b]
                thisDiff = rd(round(thisG - thisP,5),2)
                thisRow = pandas.DataFrame([[fightCode, thisG, thisP, thisDiff]],columns=colSetGminusP)
                outDF = pandas.concat([outDF,thisRow], ignore_index=True)
    return outDF

def getKendallsW(jurorDFSet, k):
    ''' k - число команд, 
        m - число жюри,
        Ravg - средний ранг команд,
        arr_Ri - суммарный ранг команды,
        RSD - сумма квадратов отклонений Ri от Ravg
        '''
    jurorRanks = [df.sort_values('Team', ignore_index=True) for df in jurorDFSet]

    #checking for ties
    ts = []
    for juror_rank_table in jurorRanks:
        tj = [juror_rank_table.Rank[juror_rank_table.Rank==r].count() for r in set(juror_rank_table.Rank.tolist()) if juror_rank_table.Rank[juror_rank_table.Rank==r].count()>1]
        ts.append(tj)
    num_T = 0
    for tj in ts:
        for tg in tj:
            num_T += tg**3 - tg

    #calculating
    arr_Ri=[]
    m = len(jurorDFSet)
    for teamCode in teamCodes[0:k]:
        num_Ri = 0
        i = teamCodes.index(teamCode)
        for jurorRank in jurorRanks:
            num_Ri += jurorRank.Rank[i]
        arr_Ri.append(num_Ri)
        
    num_S2 = sum([x**2 for x in arr_Ri])
    num_Ravg = sum(arr_Ri)/k
    num_RSD=sum([(Ri-num_Ravg)**2 for Ri in arr_Ri])
    num_W = rd( ((12*num_S2) - 3*k*(m**2)*((k+1)**2))/((m**2)*(k**3-k)-(m*num_T)) , 3)
    return num_W

def get_rho(fight_df):
    reps0 = [0, 3, 6, 9]
    p_row = fight_df.tail(1).squeeze()
    fight_df.drop(fight_df.tail(1).index,inplace=True)
    fight_df.dropna(axis='columns', inplace=True)
    num = fight_df.shape[0]
    sigma2s=[]

    for i in range(3):
        reps = [x+i for x in reps0 if x+1<fight_df.shape[1]] #i=0 - reps, i=1 - opps, i=2 - revs
        sigma2s.append(0)
        grade_count = 0
        
        for col in fight_df.iloc[:,reps]:
            grades = fight_df[col].squeeze()
            half = rd((grades.max() + grades.min())/2, 1)
            grades.drop([grades.idxmax(), grades.idxmin()], inplace=True)
            grades = grades.append(pandas.Series([half]),ignore_index=True)

            for grade in grades:
                sigma2s[i] += rd((p_row[col] - grade)**2,3)
                grade_count += 1

    sigma2s = [rd(s/grade_count, 3) for s in sigma2s] #REP, OPP, REV
    sigma2SP = rd(sum(sigma2s), 3)
    rho = rd(sqrt(sigma2SP / (num-1)),3)
    return rho

@welcome
def main():
    print('Data has been received')
    dataTable = pandas.read_excel(gradesHistoryFile)
    splittedData = cleanUp(splitByEmptyRow(dataTable))
    print('Cleanup completed')
    
    print('Generating output DataFrames... ', end='')
    outDataGMinusP = pandas.DataFrame(columns=colSetGminusP) 
    outData = pandas.DataFrame(columns=colSet)
    print('completed')
    
    prBar = IncrementalBar('Processing data', max = len(splittedData))
    
    #iterating through fights
    fightCalc = 0
    for aFight in splittedData:      
        fightCalc += 1
        prBar.next()
        corOrder = 0
        corWinner = 0
        num_NOrder = 0
        num_NWinner = 0
        num_SP = [0,0,0,0]
        
        #Getting fight code
        fightCode = aFight.iloc[0][0]

        #Cleaning up
        aFight = cleanUpFight(aFight)
        
        num_N = len(aFight.iloc[:, 1])
        
        #Calculating SPs
        teamCols = getFightType(aFight)
        teamsNum = getTeamNum(aFight)
        rowP = pandas.Series(index=aFight.columns, dtype='float64') #get an empty row ready to contain P's

                #D
        if fightCalc == 1:
            print(teamCols)
            print(teamsNum)
            print(aFight)

        #Coefficients
        if config.is_IYPT:
            colList = [0,3,6,9]
            for i in range(2):
                aFight.iloc[:, [col+i for col in colList]] *= (3-i)

        for this_col in aFight:
            currCol = aFight[this_col]        
            if currCol.count() != 0:
                currCol = currCol.astype(int)
                num_P = findP(currCol) 
                rowP[this_col] = num_P
        aFight = aFight.append(rowP, ignore_index=True)

        outDataGMinusP = pandas.concat([outDataGMinusP,headToGMinusPTable(aFight, fightCode)],ignore_index=True)

        num_rho = get_rho(aFight)
        
        for i in range(4):
            num_SP[i] += rd(aFight.iloc[-1, teamCols[i]].sum(),1)
        
        teamSPs = pandas.DataFrame({'Team': teamCodes,
                                    'SP': num_SP})
        
        teamSPs = giveRanks(teamSPs)
        
        #Calculating juror DFs with SPs
        jurorSPs = []
        for j in range(num_N):
            num_SPJ = [0,0,0,0]
            for i in range(4):
                num_SPJ[i] += rd(aFight.iloc[j, teamCols[i]].sum(),1)
            jurorDF = pandas.DataFrame({'Team': ['A','B','C','D'],
                                        'SP': num_SPJ})
            jurorSPs.append(giveRanks(jurorDF))             
        
        #Sending to W obtainer
        num_W = getKendallsW(jurorSPs, teamsNum)
        
        #Counting matching jurors
        teamSPsorted = teamSPs
        for j in range(num_N):
            jurorDFsorted = jurorSPs[j]
            jOrder = (jurorDFsorted.Team.tolist() == teamSPsorted.Team.tolist()) and (jurorDFsorted.Rank.tolist() == teamSPsorted.Rank.tolist())
            jWinner = (jurorDFsorted.head(1).Team.tolist() == teamSPsorted.head(1).Team.tolist()) and (jurorDFsorted.head(1).Rank.tolist() == teamSPsorted.head(1).Rank.tolist())
            num_NWinner += int(jWinner)
            num_NOrder += int(jOrder)
        
        corOrder = rd(num_NOrder/num_N, 3)
        corWinner = rd(num_NWinner/num_N,3)
        
        localData = pandas.DataFrame([[fightCode, teamsNum, num_N, num_NOrder, num_NWinner, corOrder, corWinner, num_W, num_rho]], columns=colSet)
        outData = pandas.concat([outData, localData], ignore_index=True)
    
    prBar.finish()
    outData.to_csv(outFile,sep = '\t',index = False)
    outDataGMinusP.to_csv(outFileGminusP, sep='\t',index=False)
    print('Processed',fightCalc,'fights successfully:', fightCalc==len(splittedData))
    print(outFile, 'and', outFileGminusP, 'files created')


if __name__ == "__main__":
    main()