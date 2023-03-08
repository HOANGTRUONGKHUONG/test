from builtins import getattr
from app.model import WebsiteBase, ExceptionBase,GroupWebsiteBase,WebsiteHaveCRS,WebsiteHaveRuleOther\
    ,WebsiteHaveTrustwave,AntiVirusHaveWebsite,CRSBase,TrustwaveBase,RuleOtherBase,AntiVirusBase
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.http.response import *
from app.libraries.configuration.web_server import *
import re,shutil
from app.libraries.logger import c_logger



FILE_PATH = "/usr/local/openresty/nginx/conf.d"
site_other_path = "/home/bwaf/bwaf/app/libraries/configuration/site_other.temp"
detect_mode_path= "/home/bwaf/bwaf/app/libraries/configuration/detect_only.conf"
tables_web_have=[WebsiteHaveCRS,WebsiteHaveTrustwave,WebsiteHaveRuleOther,AntiVirusHaveWebsite]
tables_rule_content=[CRSBase,TrustwaveBase,RuleOtherBase,AntiVirusBase]
name_ids=[WebsiteHaveCRS.crs_id,WebsiteHaveTrustwave.trust_id,WebsiteHaveRuleOther.rule_other_id,AntiVirusHaveWebsite.anti_id]

 
    
def from_database_to_file():
    session,engine_connect = ORMSession_alter()
    #group website
    all_id_group_website = session.query(GroupWebsiteBase.id).all()
    for id in all_id_group_website:
        data_group_website = session.query(GroupWebsiteBase).filter(
            GroupWebsiteBase.id.__eq__(re.sub(r"[^a-zA-Z0-9]","",str(id)))).first()
        data_website_name= session.query(WebsiteBase.website_domain).filter(
            WebsiteBase.group_website_id.__eq__(id)).all()
        id_website_group = session.query(WebsiteBase.id).filter(
            WebsiteBase.group_website_id.__eq__(id)).all()
        # print (type(id_website_group))

        # when debug status ON(detectOnly)
        try:
         #   print (data_group_website.__dict__)
            if data_group_website.group_website_status == 0:
         #       print ("WAF STT = 0")
                for website in data_website_name:
                    website=re.sub(r"[^a-zA-Z0-9.]","",str(website))
                    # print (website)
                    web_file = open(f'{FILE_PATH}/{website}.conf','r')
                    web_file_lines = web_file.readlines()
                    for i in range(len(web_file_lines)):
                        if web_file_lines[i].strip() == f"#include {detect_mode_path};":
                #            print("del cmt")
                            web_file_lines[i] =  web_file_lines[i].lstrip().replace("#","")
                  #          print (web_file_lines[i])
                            web_file.close()
                            # print (web_file_lines)
                            web_file = open(f'{FILE_PATH}/{website}.conf','w')
                            web_file.writelines(web_file_lines)
                            web_file.close()         
            #when debug status OFF                             
            elif data_group_website.group_website_status == 1:
                for website in data_website_name:
                    data= session.query(WebsiteBase).filter(
                        WebsiteBase.website_domain.__eq__(website)
                    ).first()
                    if data.website_status==0:
                        website=re.sub(r"[^a-zA-Z0-9.]","",str(website))
                        #print (website)
                        web_file = open(f'{FILE_PATH}/{website}.conf','r')
                        web_file_lines = web_file.readlines()
                        for i in range(len(web_file_lines)):
                            # print (line)
                            if web_file_lines[i].strip() == f"#include {detect_mode_path};":
                                web_file_lines[i] =  web_file_lines[i].lstrip().replace("#","")
                                # print (web_file_lines[i])
                                web_file.close()
                                # print (web_file_lines)
                                web_file = open(f'{FILE_PATH}/{website}.conf','w')
                                web_file.writelines(web_file_lines)
                                web_file.close()
                    elif data.website_status == 1:
                        website=re.sub(r"[^a-zA-Z0-9.]","",str(website))
                        # print (website)
                        web_file = open(f'{FILE_PATH}/{website}.conf','r')
                        web_file_lines = web_file.readlines()
                        for i in range(len(web_file_lines)):
                            # print (line)
                            # print(web_file_lines[i])
                            if web_file_lines[i].strip() == f"include {detect_mode_path};":
                                web_file_lines[i] = "#" + web_file_lines[i].lstrip()
                                # print (web_file_lines[i])
                                web_file.close()
                                # print (web_file_lines)
                                web_file = open(f'{FILE_PATH}/{website}.conf','w')
                                web_file.writelines(web_file_lines)
                                web_file.close()
        except Exception as e:
            raise e    
    # #END
    #Turn on/off rule in website
        try:
            for website_name,website_id in zip(data_website_name,id_website_group):
                website_name = re.sub(r"[^a-zA-Z0-9.]","",str(website_name))
                website_id=re.sub(r"[^0-9]","",str(website_id))
                # print (id_web)
                total=''
                for table_web_have,table_rule_content, name_id in zip(tables_web_have,tables_rule_content,name_ids):
                    # print (table_web_have,table_rule_content, name_id)
                    many_rule = session.query(name_id,table_web_have.rule_status).filter(
                            table_web_have.website_id.__eq__(website_id)).all()
                    # print (crs_rule)
                    if table_rule_content == RuleOtherBase:
                        for a,b in many_rule:
                            # print(a,b)
                            content_rule = session.query(table_rule_content.id).filter(table_rule_content.id.__eq__(a)).first()
                            if content_rule is not None:
                                a=re.sub(r"[^0-9]","",str(content_rule))
                                if b == 0:
                                    # print("removebyID "+ a)
                                    total = total + 'SecRuleRemoveById ' +a +'\n'
                            #     if b == 1:
                            #         print("notremovebyID "+ a)
                                    
                            # else:
                            #     print ('rule not found')
                                
                    else:
                        for a,b in many_rule:
                            # print(a,b)
                            content_rule = session.query(table_rule_content.id_rule).filter(table_rule_content.id.__eq__(a)).first()
                            if content_rule is not None:
                                a=re.sub(r"[^0-9]","",str(content_rule))
                                if b == 0:
                                    # print("removebyID "+ a)
                                    total = total + 'SecRuleRemoveById ' +a +'\n'
                            #     if b == 1:
                                    
                            #         print("notremovebyID "+ a)
                            # else:
                            #     return 'rule not found'
                # print (total)
                final = f"modsecurity_rules '\n {total} ';"
                off_rule=open(f'{FILE_PATH}/{website_name}/off_rule.conf','w')
                off_rule.write(final)
                off_rule.close()
        except Exception as e:
            return status_code_400(e)
    # #END            
            
    # Modify Exception 
        try:
            for website_name,website_id in zip(data_website_name,id_website_group):
                # print(website_name,website_id)
                website_name = re.sub(r"[^a-zA-Z0-9.]","",str(website_name))
                website_id=re.sub(r"[^0-9]","",str(website_id))
                list_file=os.listdir(f'{FILE_PATH}/{website_name}')
                # print (list_file)
                # get list site of website
                list_site =[]
                all_site = session.query(ExceptionBase.sites).filter(ExceptionBase.website_id.__eq__(website_id)).all()
                for sites in all_site:
                    if str(sites).count('/')==1:
                        list_site.append(re.sub(r"[^a-zA-Z0-9/]","",str(sites)))
                    elif str(sites).count('/')>1:
                        site = re.sub(r"[^a-zA-Z0-9,/]","",str(sorted(set(sites)))).split(',')
                        list_site =list_site + site
                list_site_web= list(set(list_site))
                # print("kjaskdjkas: ",list_site_web)
                total=''
                for site in list_site_web:
                    site=site.replace('/','')
                    temp_file=open(site_other_path,'r')
                    temp_file_data=temp_file.read()
                    temp_file.close()
                    # print (temp_file_data)
                    temp_file_data = temp_file_data.replace('<site>', site).replace('<website_name>',website_name)
                    total = total + temp_file_data + '\n'
                # print (total)
                file = open(f'{FILE_PATH}/{website_name}/site_other.conf','w')
                file.write(total)
                file.close
                for site in list_site_web:
                    site=site.replace('/','')
                    rules=''
                    data_site = session.query(ExceptionBase.rules,ExceptionBase.excep_status).filter(ExceptionBase.sites.like(f'%{site}%')).all()
                    for rule,status in data_site:
                        if status == 1:
                            rules= rules + rule + '\n'
                    if f'{site}.conf' in list_file:
                        shutil.copy(f'{FILE_PATH}/{website_name}/{site}.conf',
                                        f'{FILE_PATH}/{website_name}/{site}_backup.conf')
                        site_file = open(f'{FILE_PATH}/{website_name}/{site}.conf',"w")
                        site_file.write(rules)
                        site_file.close()
                    # Test configure
                        if ngx_check_config() == True:
                            os.remove(f'{FILE_PATH}/{website_name}/{site}_backup.conf')
                        else:
                            os.remove(f'{FILE_PATH}/{website_name}/{site}.conf')    
                            os.rename(f'{FILE_PATH}/{website_name}/{site}_backup.conf',
                                    f'{FILE_PATH}/{website_name}/{site}.conf')
                            return f"check your syntaxádasdasd in {site}.conf"
                    else:
                        site_file = open(f'{FILE_PATH}/{website_name}/{site}.conf',"w")
                        site_file.write(rules)
                        site_file.close()
                    # Test configure     
                        if ngx_check_config() == False:
                            os.remove(f'{FILE_PATH}/{website_name}/{site}.conf')
                            return f"check your syntax in {site}.conf"
        except Exception as e:
       #     print("error!")
            return False        
        finally:
            session.close()
            engine_connect.dispose()
            # self.engine.dispose()
# from_database_to_file()
#print("kienQT:", from_database_to_file())

