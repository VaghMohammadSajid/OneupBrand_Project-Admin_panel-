import logging 
logger = logging.getLogger(__name__)
def run_path_op(main_module,data,request,temp_list):
    
    main_module_status = request.POST.get(main_module) == "on"
    

    # if main_module_status:
    #     add_main_path(main_module=main_module)
    
    if not  main_module_status:
        for i in  data:
            run_sub_path(sub_module=i,data=data[i],request=request,temp_list=temp_list,main_module=main_module)

def run_sub_path(sub_module,data,request,temp_list,main_module):
    sub_module_status = request.POST.get(sub_module) == "on"
    logger.debug(sub_module)
    # if sub_module_status:
    #     add_sub_module_path(sub_module)

    
    
    if not sub_module_status:
        try:
            for i in data:
                if not  request.POST.get(f"{sub_module} {i}"):
                    temp_list.append((main_module,sub_module,i))
                
                
        except:
            pass





def add_main_path(main_module):
    pass


def add_sub_module_path(sub_module):
    pass


def add_sub_operation(sub,op):
    pass