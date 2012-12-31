import sys
from sklearn import linear_model
from sklearn import cross_validation
from sklearn import metrics


ACTIVE_REGRESSION_MODELS = ['LinearRegressionModel']


def get_regression_class(class_name):
    cls = getattr(sys.modules[__name__], class_name)
    return cls


class BaseRegressionModel(object):

    regression_model = None
    
    def __init__(self, **options):
        self.options = options
    
    def train(self, x_data, y_data):
        raise NotImplementedError()
        
    def cv_score(self, x_data, y_data):
        raise NotImplementedError()

    def cv_results(self, x_data, y_data,cv=5):
        raise NotImplementedError()
    
    def predict(self):
        raise NotImplementedError()
        
    
class LinearRegressionModel(BaseRegressionModel):


    def train(self, x_data, y_data):

        clf = linear_model.LinearRegression()
        clf.fit(x_data, y_data)
        self.regression_model = clf
        return clf


    def cv_scores(self, x_data, y_data,cv=5):
        scores = cross_validation.cross_val_score(self.regression_model, x_data, y_data, cv=cv, score_func=metrics.mean_squared_error)
        return list(scores)


    def cv_results(self, x_data, y_data,cv=5):
        raise NotImplementedError()
