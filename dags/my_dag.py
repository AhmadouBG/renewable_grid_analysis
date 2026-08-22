from airflow.sdk import dag,task

@dag()
def my_dag():
    
    @task
    def training_model_1():
        return 1

    @task
    def training_model_2():
        return 2

    @task
    def training_model_3():
        return 3

    @task.branch
    def best_model_prediction(accuracies):
        if accuracies[0] > 2:
            return 'accurate'
        return 'unaccurate'
    
    @task.bash
    def accurate():
        return "echo 'accurate'"
    
    @task.bash
    def unaccurate():
        return "echo 'unaccurate'"
        
    accuracies = [training_model_1(), training_model_2(), training_model_3()]
    accuracies >> best_model_prediction(accuracies) >> [accurate(), unaccurate()]
    

my_dag()
    