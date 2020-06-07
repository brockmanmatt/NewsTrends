# AUTOGENERATED! DO NOT EDIT! File to edit: 02_predictive_analysis.ipynb (unless otherwise specified).

__all__ = ['predicter', 'predicter', 'predicter', 'predicter', 'predicter', 'get_mse', 'predicter']

# Cell
from newstrends import loader
import pandas as pd
from pmdarima import auto_arima
import warnings
warnings.filterwarnings("ignore")


# Cell
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np

# Cell
class predicter(loader.article_holder):

    def __init__(self):
        super().__init__()



# Cell
class predicter(predicter):
    def getOneStepForecast(self, steps:int=1, model:str="sarimax"):
        print(df.columns)
        return -1



# Cell
class predicter(predicter):
    def transformTimeSeries(self, keyword:str="", publishers:list=[], timeStart=-1, timeEnd=-1, aggregate="h"):
        if keyword == "":
            raise Exception("Pass a keyword")
        if type(keyword)!=str:
            raise Exception("Pass keyword as a string")

        df= self.df.copy()
        df = df[df.tokens.apply(lambda x: keyword in x)]

        df.date = pd.to_datetime(df.date)
        df.set_index("date", inplace=True)

        newDF = pd.DataFrame()
        for src in publishers:
            newDF[src] = df[df.source==src].resample(aggregate).count()["quickReplace"]
        df=newDF
        if len(df) < 1:
            raise Exception("No data in time series")
        self.timeDF = df.fillna(0)



# Cell
class predicter(predicter):

    def simpleSarimaxModel(self, endogenous:str, exogenous=[], indexStart=-1, indexEnd=-1, aggregate="h", m=24, ic:["oob", "aic"]="oob"):

        try:
            if len(self.train) < 1:
                raise Exception("")

        except:
            raise Exception("No transformed time series; run test_train split")


        mDict={
            "D":7,
            "h":24,
        }
        try:
            m=mDict[aggregate]
        except:
            pass

        df = self.timeDF.resample(aggregate).sum()

        if indexStart > 0:
            df=df[indexStart:]


        endo = df[[endogenous]]

        if len(exogenous) > 0:
            endo = endo[1:]
            exog = df[exogenous].shift()[1:]
            model = auto_arima(endo, exogenous=exog, out_of_sample_size=3*m, information_criterion=ic, m=m, stepwise=True, trace=True)


        else:
            model = auto_arima(endo, out_of_sample_size=24, information_criterion=ic, m=m, stepwise=True, trace=True)


        return model

# Cell
class predicter(predicter):
    "generate best model for each series in the loaded time series dataframe"
    def generateMultivarSARIMAXResults(self):
        self.multiVarResults = {}

        for publication in self.test.columns:
            #hmm, doing for arbetrary numbers, I should be able to assume that pvalues/params of i correspond
            self.multiVarResults[publication] = {}

            endogenous = publication
            exogenous = [x for x in self.test.columns if x != publication]

            endo = endo[1:]
            exog = df[exogenous].shift()[1:]
            model = auto_arima(endo, exogenous=exog, out_of_sample_size=3*m, information_criterion=ic, m=m, stepwise=True, trace=True)

            endo = self.timeDF[[endogenous]][1:].copy()
            exog = self.timeDF[exogenous].shift()[1:]

            if model.with_intercept:
                newModel = SARIMAX(endo, exog=exog, order = model.order, seasonal_order=model.seasonal_order, trend='c')
            else:
                newModel = SARIMAX(endo, exog=exog, order = model.order, seasonal_order=model.seasonal_order)

            newModel = newModel.filter(model.params())

            endo["yhat"] = newModel.predict(exogenous=exog)

            self.multiVarResults[publication]["params"] = newModel.params
            self.multiVarResults[publication]["pvalues"] = newModel.pvalues
            self.multiVarResults[publication]["results"] = endo




# Cell
def get_mse(df):
    """calculate MSE of df, assuming column1 is actual column2 is predicted"""
    true = df.columns[0]
    predicted = df.columns[1]

    return ((df[true]-df[predicted])**2).mean()

# Cell
class predicter(predicter):
    """
    It can be hard to know when to start modeling a series, how does the start date influence error?
    """
    def get_sarimax_starting_errors(self, topic="", endogSeries:str="", exogSeries:list=[], units:int=1)->pd.DataFrame:
        """
        Takes a topic, engogenous publisher (str) and possible exogenous variables
        returns errors for test set over time
        """

        results = {}

        df = self.train.copy()

        current_start = 0
        indices = df.index.to_list()
        while current_start < len(df):
            try:
                model = self.simpleSarimaxModel(endogSeries, exogenous=exogSeries, indexStart=current_start)
            except:
                break

            endo=self.timeDF[[endogSeries]][1:]

            kwargs = {}
            kwargs["order"] = model.order
            kwargs["seasonal_order"] = model.seasonal_order
            if model.with_intercept:
                kwargs["trend"]='c'
            if len(exogSeries) > 0:
                exog=timeDF[exogSeries].shift()[1:]
                kwargs["exog"] = exog

            newModel = SARIMAX(endo, **kwargs)
            newModel = newModel.filter(model.params())

            if len(exogSeries) > 0:
                endo["yhat"] = newModel.predict(exogenous=exog)
            else:
                endo["yhat"] = newModel.predict()

            scoring = self.test[[endogSeries]].copy()
            scoring["yhat"] = endo["yhat"]

            results[indices[current_start]] = scoring
            self.results = results
            current_start += units


