from shapesengine.models import *
a = DatasetDescriptor.objects.all()[0]

r = RegressionModel(descriptor = a, type='LinearRegressionModel', y_column='cpi', x_columns=['pop','year'])
x,y = r.get_training_set()

print r