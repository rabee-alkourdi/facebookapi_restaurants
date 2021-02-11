import pandas as pd
import facebook as fb
import matplotlib.pyplot as plt
import scipy.stats as sts
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.stattools import durbin_watson
import numpy as np
import json

class Facebook_Helper:

    # I/O ----------------------------------------------------- #
    def writeToFile(savePath, fileType, *data):
        print("+---------------------------------------------------------------+")
        print("Writing to {0} file. Please wait.....".format(fileType.upper()))
        if fileType.lower() == 'csv':
            data[0].to_csv(savePath)
        elif fileType.lower() == 'xlsx':
            data[0].to_excel(savePath)
        elif fileType.lower() == 'txt':
            data[0].to_csv(savePath, sep=' ', header=False)
        else:
            data[0].to_csv(savePath)
        print("Finished writing.")
        print("+---------------------------------------------------------------+")

    def readFile(filePath, fileType):
        print("+---------------------------------------------------------------+")
        print("Reading {0} file. Please wait.....".format(fileType.upper()))
        if fileType.lower() == 'csv':
            dataset = pd.read_csv(filePath, encoding='ISO-8859-1')
        elif fileType.lower() == 'xlsx':
            dataset = pd.read_excel(filePath)
        else:
            print("ERROR: Unsupported file format")
            return 
        print("Finished reading.")
        print("+---------------------------------------------------------------+")

        dataset['price_range'] = dataset['price_range'].astype('category')
        dataset['category'] = dataset['category'].astype('category')
        dataset['overall_star_rating'] = dataset['overall_star_rating'].astype('category')

        return dataset

    def rawJsonRW(filePath, operation, *data):
        if operation == 'r':
            print("+---------------------------------------------------------------+")
            print("Reading JSON file. Please wait.....")
            with open(filePath) as json_data:
                unprocessed_data = json.load(json_data)
            print("Operation complete.")
            print("+---------------------------------------------------------------+")
            return unprocessed_data
        if operation == 'w':
            print("+---------------------------------------------------------------+")
            print("Writing to JSON file. Please wait.....")
            with open(filePath, 'w') as outfile:
                json.dump(data[0], outfile)
            print("Operation complete.")
            print("+---------------------------------------------------------------+")
    # --------------------------------------------------------- #
    
    # Data Munging--------------------------------------------- #
    def countField(field, data):
        counter = 0
        for rec in data:
            if field in rec:
                counter += 1
            else:
                continue  
        print('{0}: {1}'.format(field,counter))    

    def selectAndFill(fields, subfields_parents, subfields_children, data):
        all = False
        final = []
        for record in data:
            for field in fields:
                if field in record:
                    if field in subfields_parents:
                        for child in subfields_children[subfields_parents.index(field)]:
                            if child not in record[field]:
                                record[field][child] = False
                    all = True
                else:
                    all = False
                    break  
            if all:
                final += [record]
        return final

    def convertToDF(data):
        df_fields = ['id', 'name', 'fan_count', 'talking_about_count', 'checkins', 
                     'category', 'overall_star_rating', 'price_range', 'delivery',
                     'reserve', 'waiter', 'breakfast', 'lunch', 'dinner', 'coffee', 'drinks']
        dataset = pd.DataFrame(columns = df_fields)
        
        dataset['id'] = [x['id'] for x in data]
        dataset['name'] = [x['name'] for x in data]
        dataset['fan_count'] = [x['fan_count'] for x in data]
        dataset['talking_about_count'] = [x['talking_about_count'] for x in data]
        dataset['checkins'] = [x['checkins'] for x in data]
        dataset['category'] = [x['category'] for x in data]
        dataset['overall_star_rating'] = [x['overall_star_rating'] for x in data]
        dataset['price_range'] = [x['price_range'] for x in data]
        dataset['price_range'] = dataset['price_range'].map({"$": "Under $10", 
                                                             "$$": "Between $10 - $99", 
                                                             "$$$": "Between $100 - $999", 
                                                             "$$$$": "More than $1000"})
        dataset['overall_star_rating'] = dataset['overall_star_rating'].apply(lambda x:
                                                                              "*" if (x > 1.0) & (x < 2.0)
                                                                              else "**" if (x > 2.0) & (x < 3.0)
                                                                              else "***" if (x > 3.0) & (x < 4.0)
                                                                              else "****" if (x > 4.0) & (x < 5.0)
                                                                              else "*****" if x == 5.0
                                                                              else "None")

        dataset['delivery'] = [x['restaurant_services']['delivery'] for x in data]
        dataset['reserve'] = [x['restaurant_services']['reserve'] for x in data]
        dataset['waiter'] = [x['restaurant_services']['waiter'] for x in data]

        dataset['breakfast'] = [x['restaurant_specialties']['breakfast'] for x in data]
        dataset['breakfast'] = dataset['breakfast'].map({0: False, 1: True})
        dataset['lunch'] = [x['restaurant_specialties']['lunch'] for x in data]
        dataset['lunch'] = dataset['lunch'].map({0: False, 1: True})
        dataset['dinner'] = [x['restaurant_specialties']['dinner'] for x in data]
        dataset['dinner'] = dataset['dinner'].map({0: False, 1: True})
        dataset['coffee'] = [x['restaurant_specialties']['coffee'] for x in data]
        dataset['coffee'] = dataset['coffee'].map({0: False, 1: True})
        dataset['drinks'] = [x['restaurant_specialties']['drinks'] for x in data]
        dataset['drinks'] = dataset['drinks'].map({0: False, 1: True})

        dataset = dataset.astype({'id': np.int64})
        dataset = dataset.astype({'fan_count': int})
        dataset = dataset.astype({'talking_about_count': int})
        dataset = dataset.astype({'checkins': int})

        dataset['price_range'] = dataset['price_range'].astype('category')
        dataset['category'] = dataset['category'].astype('category')
        dataset['overall_star_rating'] = dataset['overall_star_rating'].astype('category')

        # set index
        dataset = dataset.set_index('id')

        # remove duplicates
        dataset = dataset[~dataset.index.duplicated(keep='first')]

        # keep only active pages
        dataset = dataset[dataset.fan_count != 0]
        dataset = dataset[dataset.talking_about_count != 0]
        dataset = dataset[dataset.checkins != 0]

        # remove outliers
        dataset = dataset[dataset['fan_count'] < dataset['fan_count'].quantile(0.99)]
        dataset = dataset[dataset['talking_about_count'] < dataset['talking_about_count'].quantile(0.99)]
        dataset = dataset[dataset['checkins'] < dataset['checkins'].quantile(0.99)]

        return dataset
    # --------------------------------------------------------- #

    # Data Fetching-------------------------------------------- #   
    def fetchOnlineData(ACCESS_TOKEN, original_fields, query_terms):
        '''
        original_fields = ['id', 'name', 'fan_count', 'overall_star_rating', 'rating_count',
                           'category', 'restaurant_services', 'restaurant_specialties', 'awards',
                           'food_styles', 'payment_options', 'price_range', 'attire', 'current_location',
                           'talking_about_count', 'verification_status', 'checkins']
        '''

        graph = fb.GraphAPI(access_token=ACCESS_TOKEN, version = 2.10)
        unprocessed_data = []

        for term in query_terms:
            try:
                response = graph.request('search', {'q': term, 'type': 'page', 'fields': ",".join(original_fields), 'limit': 1000})
                unprocessed_data += response['data']
                print('term: {0}, retreived: {1} records'.format(term, len(response['data'])))
            except Exception:
                unprocessed_data += response['data']
                print('term: {0}, retreived: {1} records'.format(term, len(response['data'])))
                continue
        return unprocessed_data
    # --------------------------------------------------------- #

    # Analysis------------------------------------------------- #
    def relationship(dv, iv, dataset):
        pcc = sts.pearsonr(dataset[dv], dataset[iv])

        # Relationship strength
        corr = abs(pcc[0])
        if corr == 0.0:
            strength = "no"
        elif (corr > 0.0) & (corr < 0.2):        
            strength = "very weak"
        elif (corr >= 0.2) & (corr < 0.4): 
            strength = "weak"
        elif (corr >= 0.4) & (corr < 0.6): 
            strength = "moderate"
        elif (corr >= 0.6) & (corr < 0.8): 
            strength = "strong"
        elif (corr >= 0.8) & (corr < 1.0): 
            strength = "very strong"
        elif corr == 1.0: 
            strength = "perfect"

        # Relationship direction
        if pcc[0] < 0:
            direction = "negative"
        elif pcc[0] > 0:
            direction = "positive"
        else:
            direction = ""

        dataset.plot(kind="scatter", x=iv, y=dv, c='black', alpha=.3, grid=True)
        plt.xlabel(' '.join(iv.split('_')).title(), fontsize=14)
        plt.ylabel(' '.join(dv.split('_')).title(), fontsize=14)

        X = dataset[iv]
        Y = dataset[dv]
        m, b = np.polyfit(X, Y, 1)
        plt.plot(X, m*X + b, 'b-')

        description = "We notice that there is a {0} {1} linear relationship between {2} and {3} (r={4:.2f}, p={5})".format(strength, direction, iv, dv, pcc[0], pcc[1])
        plt.figtext(0.1, 0.005, description)

        plt.show()
        plt.close()

    def independent_ttest(dv, iv, dataset):
        res = ""

        ivGroups = dataset.groupby(iv)
        for name, group in ivGroups:
            if str(name) == "True":
                group1 = group[dv]
            if str(name) == "False":
                group2 = group[dv]

        diffMean = abs(group1.mean() - group2.mean())

        res += "Average {0} for {1}=True is {2:.3f}\n".format(dv, iv, group1.mean())
        res += "Average {0} for {1}=False is {2:.3f}\n".format(dv, iv, group2.mean())
        res += "Difference between {0} for {1}=True and {1}=False is {2:.3f}\n".format(dv, iv, diffMean)
        res += "\nIs this difference significant? :\n\n"

        t_observed, p_value = sts.ttest_ind(group1, group2)
        res += "t-observed = {0:.3f} and p-value = {1}\n".format(t_observed, p_value)
        t_critical = sts.t.ppf(q=0.975, df=(group1.count()+group2.count())-2)
        res += "t-critical = {0}\n".format(t_critical)

        if abs(t_observed) < t_critical:
            res += "There is no significant difference in {0} due to {1}".format(dv, iv)
        else:
            res += "There a significant difference in {0} due to {1}".format(dv, iv)

        return(res)

    def oneway_anova(dv, iv, dataset):
        res = ""

        formula = '{0} ~ {1}'.format(dv, iv)
        regression = ols(formula, data = dataset).fit()

        anova_table = sm.stats.anova_lm(regression, typ=2)

        p = anova_table['PR(>F)'][0]
        res += str(anova_table)


        etaSquared = anova_table['sum_sq'][0]/(anova_table['sum_sq'][0] + anova_table['sum_sq'][1])
        res += "\nWe can explain {0:.3f}% of {1} difference due to difference in {2}\n\n".format(etaSquared*100, dv, iv)

        if p >= 0.05:
            res += "\nThe is no significant difference in {0} between different categories of {1} ".format(dv, iv)
        else:
            res += "There is significant difference in {0} between different categories of {1}".format(dv, iv)
            res += "\nThere are at least two groups different. which two? :\n\n"
            res += "\nPost-Hoc Test:-----------------------\n"
            tukey = pairwise_tukeyhsd(endog=dataset[dv],    
                                      groups=dataset[iv],       
                                      alpha=0.05)             

            res += str(tukey.summary())          

        return res

    def twoway_anova(dv, iv1, iv2, dataset):
        res = ""

        formula = '{0} ~ {1} + {2} + {1}:{2}'.format(dv, iv1, iv2)
        regression = ols(formula, data = dataset).fit()

        anova_table = sm.stats.anova_lm(regression, typ=2)

        p_1 = anova_table['PR(>F)'][0]
        p_2 = anova_table['PR(>F)'][1]
        p_total = anova_table['PR(>F)'][2]
        res += str(anova_table)


        etaSquared_1 = anova_table['sum_sq'][0]/(anova_table['sum_sq'][0] + anova_table['sum_sq'][3])
        etaSquared_2 = anova_table['sum_sq'][1]/(anova_table['sum_sq'][1] + anova_table['sum_sq'][3])
        etaSquared_total = anova_table['sum_sq'][2]/(anova_table['sum_sq'][2] + anova_table['sum_sq'][3])
        res += "\nWe can explain {0:.3f}% of {1} difference due to difference in {2}\n".format(etaSquared_1*100, dv, iv1)
        res += "\nWe can explain {0:.3f}% of {1} difference due to difference in {2}\n".format(etaSquared_2*100, dv, iv2)
        res += "\nWe can explain {0:.3f}% of {1} difference due to difference in {2} and {3}\n\n".format(etaSquared_total*100, dv, iv1, iv2)

        if p_1 >= 0.05:
            res += "\nThe is no significant difference in {0} between different categories of {1}".format(dv, iv1)
        else:
            res += "\nThere is significant difference in {0} between different categories of {1}".format(dv, iv1)

        if p_2 >= 0.05:
            res += "\nThe is no significant difference in {0} between different categories of {1}".format(dv, iv2)
        else:
            res += "\nThere is significant difference in {0} between different categories of {1}".format(dv, iv2)

        if p_total >= 0.05:
            res += "\nThe is no significant difference in {0} between different categories of {1} and {2}".format(dv, iv1, iv2)
        else:
            res += "\nThere is significant difference in {0} between different categories of {1} and {2}".format(dv, iv1, iv2)
            res += "\nThere are at least two groups different. which two? :\n\n"
            res += "\nPost-Hoc Test:-----------------------\n"
            tukey_1 = pairwise_tukeyhsd(endog=dataset[dv],    
                                      groups=dataset[iv1],       
                                      alpha=0.05)             
            tukey_2 = pairwise_tukeyhsd(endog=dataset[dv],    
                                      groups=dataset[iv2],       
                                      alpha=0.05) 

            res += str(tukey_1.summary())     
            res += "\n-------------------------------------\n"
            res += str(tukey_2.summary())      
        return res

    def liner_regression(dv, iv1, iv2, dataset):
        res = ""

        X = np.column_stack((dataset[iv1], dataset[iv2]))
        X = sm.add_constant(X)
        Y = dataset[dv]
        model = sm.OLS(Y, X)
        result = model.fit()
        const = result.params[0]
        x1_coef = result.params[1]
        x2_coef = result.params[2]

        r_squared = result.rsquared
        p_overall = result.f_pvalue
        dw_value = durbin_watson(result.resid)
        p_values = result.pvalues

        res += str(result.summary())

        res += "\n\nLinear Regression equation between ({0} 'Y') and ({1} 'X1', {2} 'X2') is:\n".format(dv, iv1, iv2)
        res += "+----------------------------------+\n"
        res += "| Y = {0:.3f} + {1:.3f}*X1 + {2:.3f}*X2  |\n".format(const, x1_coef, x2_coef)
        res += "+----------------------------------+\n"

        res += ">>> This equation indicates that {0} is predicted to increase by {1:.3f} when the {2} variable\n".format(dv, x1_coef, iv1)
        res += "goes up by one, and increase by {0:.3f} when the {1} variable goes up by one and is predicted to be\n".format(x2_coef, iv2)
        res += "{0:.3f} when both variables are at zero.\n".format(const)
        
        res += "\n>>> {0:.3f}% of the variations in the {1} are accounted for (predicted by) the {2} and {3}.\n".format(r_squared*100, dv, iv1, iv2)

        if p_overall < 0.05:
            res += "\n>>> the overall p-value {0} is less than 0.05 which means we can reject the \nnull hypothesis ({1} and {2} are not correlated to {3}).\n".format(p_overall, iv1, iv2, dv)
        else:
            res += "\n>>> the overall p-value {0} is less than 0.05 which means we can accept the \nnull hypothesis ({1} and {2} are not correlated to {3}).\n".format(p_overall, iv1, iv2, dv)
        
        if p_values[1] > p_values[2]:
            res += "\n>>> the individual p-values indicate that {0} has a higher impact on {1} than {2}.\n".format(iv2,dv,iv1)
        elif p_values[2] > p_values[1]:
            res += "\n>>> the individual p-values indicate that {0} has a higher impact on {1} than {2}.\n".format(iv1,dv,iv2)
        else:
            res += "\n>>> the individual p-values indicate that {0} and {1} has the same impact on {2}.\n".format(iv1,iv2,dv)

        dw_val_str = ""
        dw_val_meaning= ""
        if dw_value == 0.0:
            dw_val_str = "is 0"
            dw_val_meaning = "perfect positive autocorrelation"
        elif (dw_value > 0.0) & (dw_value < 0.5):
            dw_val_str = "approaches 0"
            dw_val_meaning = "strong positive autocorrelation"
        elif (dw_value >= 0.5) & (dw_value < 1.0):
            dw_val_str = "approaches 0"
            dw_val_meaning = "moderate positive autocorrelation"
        elif (dw_value >= 1.0) & (dw_value < 1.5):
            dw_val_str = "approaches 2"
            dw_val_meaning = "weak positive autocorrelation"
        elif (dw_value >= 1.5) & (dw_value < 2.0):
            dw_val_str = "approaches 2"
            dw_val_meaning = "very weak positive autocorrelation"
        elif dw_value == 2.0:
            dw_val_str = "is 2"
            dw_val_meaning = "no autocorrelation"
        elif (dw_value > 2.0) & (dw_value < 2.5):
            dw_val_str = "approaches 2"
            dw_val_meaning = "very weak negative autocorrelation"
        elif (dw_value >= 2.5) & (dw_value < 3.0):
            dw_val_str = "approaches 2"
            dw_val_meaning = "weak negative autocorrelation"
        elif (dw_value >= 3.0) & (dw_value < 3.5):
            dw_val_str = "approaches 4"
            dw_val_meaning = "moderate negative autocorrelation"
        elif (dw_value >= 3.5) & (dw_value < 4.0):
            dw_val_str = "approaches 4"
            dw_val_meaning = "strong negative autocorrelation"
        elif dw_value == 4.0:
            dw_val_str = "is 4"
            dw_val_meaning = "perfect negative autocorrelation"

        res += "\n>>> Durbin-Watson value is {0} which indicates {1} between the residuals.\n".format(dw_val_str, dw_val_meaning)

        res += "\n>>> We can have a 95% confidence in the model accuracy.\n"

        return res
    # --------------------------------------------------------- #