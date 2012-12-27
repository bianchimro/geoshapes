#Bugs
- Shape import not working

## New features

- table smart filter #ok - complete filter and use name
- queryset export feature #basic ok
- dataset export #basic ok
- table export #basic ok
- map attributes #ok, in popup
- map edit
- Visualizations
- In the datasetdescriptor model ,source should be optional (it should be possibile to create a dataset without a source)
- Celery or cueless should be used to manage long running ajax calls: 
  
  https://zapier.com/blog/2012/01/30/async-celery-example-why-and-how/



## Utils
- Modal dialog should handle confirm
- Modal dialog should be updatable with message after it has been shown
- Error messages should be propagated to modal dialogs

## Refine
- reset fields ordering
- A link to the originating source (if any) should be provided on each dataset page


## Content and public site
- Formats page
- Page to create dataset, button in datasets view
- menus for logged user
- download bootswatches

## FUTURE
- a dataset should be a set of tables
- enable relations between tables
