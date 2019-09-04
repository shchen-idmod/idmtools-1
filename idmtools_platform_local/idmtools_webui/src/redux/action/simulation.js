import {GET_SIMULATIONS, SET_SIMULATION_FILTER, LOADING_SIMULATION} from "../actionTypes";
import {handleResponse} from "../../utils/utils";
import {showError, showInfo} from "./messaging";



function receiveSimulations(data) {
    return {
        type:GET_SIMULATIONS,
        data,
        complete:true
    }

}

export function loading(loading) {
  return {
    type:LOADING_SIMULATION,
    loading
  }
}


export function fetchSimulations() { 

  
    let url = "/api/simulations";

    
    
    return (dispatch) => {

        dispatch(loading(true));
        
        return fetch(url)
            .then(response => {
  
              handleResponse(response,
                (subjects)=>{ /*success handler*/                
                  dispatch(receiveSimulations(subjects));
                  dispatch(loading(false));
                },
                (data)=> { /* failure handler */
                  dispatch(showError(data));
                })
  
            });
    };
  }



export function cancelSimulation(id) { 

  
    let url = "/api/simulations/"+id;
  
    
    return (dispatch) => {
        
        return fetch(url, {
                method: 'PUT',
                body:'{"status":"canceled"}',
                headers:{
                    'Content-Type': 'application/json'
                  }
            })
            .then(response => {
  
              handleResponse(response,
                (subjects)=>{ /*success handler*/                
                  dispatch(showInfo("Cancel operation is complete"))
                },
                (data)=> { /* failure handler */
                  dispatch(showError(data));
                })
  
            });
    };
  }


  export function setFilter(start, end) {
    return {
      type: SET_SIMULATION_FILTER,
      start, end
    }
  }
