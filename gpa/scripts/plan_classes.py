from queue import PriorityQueue
import copy
import csv
global data_file_name
data_file_name = "./uiuc-gpa-dataset.csv"
class Course:
	def __init__(self,**kwargs):
		self.__dict__ = kwargs
		if not hasattr(self, "Weight"):
			self.Weight = 4
		self.id = self.Subject.lower() + str(self.Number)
	
	def __str__(self):
		return "Course(" + str(self.__dict__)[1:-1] + ")"

	def __cmp__(self, other):
		return True

	def __repr__(self):
		return self.__str__()
class Program:
	def __init__(self, courses, course_requirements):
		self.courses = courses
		self.course_requirements = course_requirements

	
	def get_best_path(self, path_rules, iii=[], top_n=16):
		'''
		path_rules: [path_rule]: defines rules which must all be true for a given path.
		returns the path which: 
					1) minimizes number of semesters,
					2) minimizes number of courses,
					3) maximizes average gpa
		in that order.
		'''
		top=[]
		iiiids=[x.id for x in iii]
		iiiids.sort()
		existing_paths = set(''.join(iiiids))
		q = PriorityQueue()
		best_path = Path(self, iii, path_rules)
		q.put((best_path.score(), best_path))
		count=0
		prev_best = best_path
		while top_n>len(top):
			while not self.validate_path(best_path):
				count+=1
				count = count%10000
				if count == 0:
					x=[i.id for i in best_path.courses]
					print(x)
					print(len(x))
					print('')
				for course in self.courses:
					new_path = best_path.add_course(course, existing_paths)
					if new_path:
						#print("putting "+str((new_path.score(), new_path)))
						q.put((new_path.score(), new_path))
				if q.empty():
					raise Exception("Empty queue")
				prev_best = best_path
				best_path = q.get()[1]
				#print(best_path)
			top.append(best_path)
			best_path=prev_best
		return top
	
	def validate_path(self, path):
		for course_requirement in self.course_requirements:
			if not course_requirement(path.courses):
				return False
		return True

class Path:
	def __init__(self, program, courses, path_rules=None):
		self.validate(courses, path_rules)
		self.program = program
		self.path_rules = path_rules
		self.courses = courses
		
	def add_course(self, course, existing_paths):
		courses = copy.copy(self.courses)
		courses.append(course)
		courses_hash = self.hash_courses(courses)
		#print("course ="+str(course))
		#print("courses_hash="+str(courses_hash))
		#print("existing_paths="+str(existing_paths))
		if courses_hash not in existing_paths:
			try:
				ret = Path(self.program, courses, self.path_rules)
				existing_paths.add(courses_hash)
				return ret
			except Exception as e:
				pass
		return None
		
	def hash_courses(self, courses):
		ids=[i.id for i in courses]
		ids.sort()
		return ''.join(ids)
	
		
	def validate(self, courses, path_rules):
		ids = set()
		if len(courses) > 8:
			raise  Exception("8 is enough")
		for course in courses:
			id = course.id
			if id in ids:
				raise Exception("Course " + id + "is taken twice")
			ids.add(id)
		for path_rule in path_rules:
			path_rule(courses)

	def score(self):
		term_to_num = {"Spring":0, "Fall":2, "Summer":1}
		num_semesters = 0
		courses = self.courses
		if len(courses) == 0:
			return 0
		average_gpa = 0
		num_courses = len(courses)
		weight_sum  = 0.0
		for c in courses:
			c_semester = (c.Year-2020)*3 + term_to_num[c.Term]
			num_semesters = max([num_semesters, c_semester])
			average_gpa += c.Weight + c.Average_Gpa
			weight_sum  += c.Weight
		average_gpa = average_gpa/weight_sum
		score = (1000000 * num_semesters) + (1000*num_courses) + (-1*average_gpa)
		return score
		
	def __str__(self):
		return "Path" + str(self.courses)

	def __cmp__(self, other):
		return True
	
	def __repr__(self):
		return self.__str__()

	def __lt__(self, other):
		return True
def make_prereq_rule(fst_cls_id, snd_cls_id):
	def rule(courses):
		term_to_num = {"Spring":0, "Fall":2, "Summer":1}
		snd_crs_lst = [i for i in courses if i.id == snd_cls_id]
		if len(snd_crs_lst) > 0:
			snd_crs_time_val = int(snd_crs_lst[0].Year) + .1 * term_to_num[snd_crs_lst[0].Term]
			fst_crs_lst = [i for i in courses if i.id == fst_cls_id]
			if len(fst_crs_lst) > 0:
				fst_crs_time_val = int(fst_crs_lst[0].Year) + .1 * term_to_num[fst_crs_lst[0].Term]
				if snd_crs_time_val <  fst_crs_time_val:
					raise Exception(fst_cls_id + " must be taken before " + snd_cls_id)
	return rule

def make_enforce_max_courses_per_term(maxx):
	def rule(courses):
		if len(courses) == 0:
			return
		courses_per_term = {}
		for course in courses:
			yt = course.YearTerm
			if yt not in courses_per_term:
				courses_per_term[yt] = 1
			else:
				courses_per_term[yt] += 1
		if max(courses_per_term.values()) > maxx:
			raise Exception("Year-Term " + str(yt) + " has more than " + str(maxx) + "classes")
	return rule

def make_hours_requiment(hours):
	def rule(courses):
		s = sum([course.Weight for course in courses])
		if s < hours:
			return False
		return True
	return rule

def make_rule_must_do_n_of_subset(n, subset):
	'''
	n: integer, # of classes which must be done from subset
	subset: set(ids), list of class ids
	'''
	def rule(courses):
		return len(set([course.id for course in courses]).intersection(subset)) >= n
	
	return rule

def make_rule_min_num_courses(n):
	def rule(courses):
		return len(courses) == n
	return rule
global uiuc_mcs_courses
uiuc_mcs_courses = []

def get_course_data(subject, number, course_title):
	number = str(number)[0:3]
	xxx = ["A+","A","A-","B+","B","B-","C+","C","C-","D+","D","D-","F"]
	scores={i:0 for i in xxx}
	score_to_gpa={"A+":4.0,"A":4.0,"A-":3.7,"B+":3.3,"B":3.0,"B-":2.7,"C+":2.3,"C":2.0,"C-":1.7,"D+":1.3,"D":1.0,"D-":0.7,"F":0.0}
	with open(data_file_name, "r", errors='ignore') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row["Subject"].lower() == subject.lower() and str(row["Number"]) == number and row["Course Title"].lower() == course_title.lower():
				for k in scores.keys():
					scores[k] += int(row.get(k, 0))
	num_scores = float(sum([scores[k] for k in scores]))
	average_gpa = sum(score_to_gpa[k]*scores[k] for k in scores)/num_scores if num_scores > 0 else 3.5277
	return {"Average_Gpa": average_gpa, "Subject": subject, "Number": number, "Course Title": course_title}

def make_class(subject, number, course_title, term, year):
	number = str(number)
	course_data = get_course_data(subject, number, course_title)
	course_data["Term"] = term
	course_data["Year"] = year
	course_data["YearTerm"] = str(year) + term
	#print(course_data.get("Average_Gpa",None))
	#uiuc_mcs_courses.append(Course(**course_data))
	
	course = Course(**course_data)
	print(course_data)
	uiuc_mcs_courses.append(course)


# Make 2 Years worth of Courses
'''
make_class("CS", "498aml", "Applied Machine Learning", "Spring", 2021)
make_class("CS", 445, "Computational Photography", "Spring", 2020)
make_class("CS", 410, "Text Information Systems", "Fall", 2020)
make_class("CS", 410, "Text Information Systems", "Fall", 2021)
make_class("CS", 411, "Database Systems", "Spring", 2020)
make_class("CS", 411, "Database Systems", "Spring", 2021)
make_class("CS", 412, "Introduction to Data Mining", "Spring", 2020)
make_class("CS", 412, "Introduction to Data Mining", "Spring", 2021)
make_class("CS", "498dv", "Data Visualization", "Summer", 2020)
make_class("CS", "498dv", "Data Visualization", "Summer", 2021)
make_class("CS", 425, "Cloud Computing Concepts", "Fall", 2020)
make_class("CS", 425, "Cloud Computing Concepts", "Fall", 2021)
make_class("CS", "498cca", "Cloud Computing Applications", "Spring", 2020)
make_class("CS", "498cca", "Cloud Computing Applications", "Spring", 2021)
make_class("CS", "498cn", "Cloud Networking", "Fall", 2020)
make_class("CS", "498cn", "Cloud Networking", "Fall", 2021)
make_class("CS", 513, "Theory and Practice of Data Cleaning", "Summer", 2020)
make_class("CS", 513, "Theory and Practice of Data Cleaning", "Summer", 2021)
make_class("CS", "598fdc", "Foundations of Data Curation", "Fall", 2020)
make_class("CS", "598fdc", "Foundations of Data Curation", "Fall", 2021)
make_class("CS", "598psl", "Practical Statistical Learning", "Fall", 2020)
make_class("CS", "598psl", "Practical Statistical Learning", "Fall", 2021)
make_class("CS", "598ccc", "Cloud Computing Capstone", "Fall", 2020)
make_class("CS", "598ccc", "Cloud Computing Capstone", "Fall", 2021)
make_class("CS", "598ccc", "Cloud Computing Capstone", "Summer", 2020)
make_class("CS", "598ccc", "Cloud Computing Capstone", "Summer", 2021)
make_class("CS", "598dmc", "Data Mining Capstone", "Summer", 2020)
make_class("CS", "598dmc", "Data Mining Capstone", "Summer", 2021)
make_class("CS", "598dmc", "Data Mining Capstone", "Spring", 2020)
make_class("CS", "598dmc", "Data Mining Capstone", "Spring", 2021)
make_class("CS", "598abm", "Advanced Bayesian Modeling", "Spring", 2020)
make_class("CS", "598abm", "Advanced Bayesian Modeling", "Spring", 2021)
make_class("CS", 418, "Interactive Computer Graphics", "Spring", 2020)
make_class("CS", "421", "Programming Languages and Compilers", "Summer", 2020)
make_class("CS", "421", "Programming Languages and Compilers", "Summer", 2021)
make_class("CS", 427, "Software Engineering I", "Fall", 2020)
make_class("CS", 427, "Software Engineering I", "Fall", 2021)
make_class("CS", 450, "Numerical Analysis", "Fall", 2020)
make_class("CS", 450, "Numerical Analysis", "Fall", 2021)
make_class("CS", 450, "Numerical Analysis", "Spring", 2020)
make_class("CS", 450, "Numerical Analysis", "Spring", 2021)
make_class("CS", 484, "Parallel Computing", "Spring", 2020)
make_class("CS", 484, "Parallel Computing", "Spring", 2021)
make_class("CS", "498iot", "Internet of Things", "Spring", 2020)
make_class("CS", "498iot", "Internet of Things", "Spring", 2021)
make_class("STAT", 420, "Methods of Applied Statistics", "Summer", 2020)
make_class("STAT", 420, "Methods of Applied Statistics", "Summer", 2021)
'''
precomputed_data = [{'Average_Gpa': 3.7800706713780925, 'Subject': 'CS', 'Number': '498aml', 'Course Title': 'Applied Machine Learning', 'Term': 'Spring', 'Year': 2021, 'YearTerm': '2021Spring'},
{'Average_Gpa': 3.5586826347305385, 'Subject': 'CS', 'Number': '445', 'Course Title': 'Computational Photography', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.836230110159118, 'Subject': 'CS', 'Number': '410', 'Course Title': 'Text Information Systems', 'Term': 'Fall', 'Year': 2020, 'YearTerm': '2020Fall'},
{'Average_Gpa': 3.836230110159118, 'Subject': 'CS', 'Number': '410', 'Course Title': 'Text Information Systems', 'Term': 'Fall', 'Year': 2021, 'YearTerm': '2021Fall'},
{'Average_Gpa': 3.2926649076517154, 'Subject': 'CS', 'Number': '411', 'Course Title': 'Database Systems', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.2926649076517154, 'Subject': 'CS', 'Number': '411', 'Course Title': 'Database Systems', 'Term': 'Spring', 'Year': 2021, 'YearTerm': '2021Spring'},
{'Average_Gpa': 3.3060378847671665, 'Subject': 'CS', 'Number': '412', 'Course Title': 'Introduction to Data Mining', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.3060378847671665, 'Subject': 'CS', 'Number': '412', 'Course Title': 'Introduction to Data Mining', 'Term': 'Spring', 'Year': 2021, 'YearTerm': '2021Spring'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '498dv', 'Course Title': 'Data Visualization', 'Term': 'Summer', 'Year': 2020, 'YearTerm': '2020Summer'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '498dv', 'Course Title': 'Data Visualization', 'Term': 'Summer', 'Year': 2021, 'YearTerm': '2021Summer'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '425', 'Course Title': 'Cloud Computing Concepts', 'Term': 'Fall', 'Year': 2020, 'YearTerm': '2020Fall'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '425', 'Course Title': 'Cloud Computing Concepts', 'Term': 'Fall', 'Year': 2021, 'YearTerm': '2021Fall'},
{'Average_Gpa': 3.823529411764706, 'Subject': 'CS', 'Number': '498cca', 'Course Title': 'Cloud Computing Applications', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.823529411764706, 'Subject': 'CS', 'Number': '498cca', 'Course Title': 'Cloud Computing Applications', 'Term': 'Spring', 'Year': 2021, 'YearTerm': '2021Spring'},
{'Average_Gpa': 3.1666666666666665, 'Subject': 'CS', 'Number': '498cn', 'Course Title': 'Cloud Networking', 'Term': 'Fall', 'Year': 2020, 'YearTerm': '2020Fall'},
{'Average_Gpa': 3.1666666666666665, 'Subject': 'CS', 'Number': '498cn', 'Course Title': 'Cloud Networking', 'Term': 'Fall', 'Year': 2021, 'YearTerm': '2021Fall'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '513', 'Course Title': 'Theory and Practice of Data Cleaning', 'Term': 'Summer', 'Year': 2020, 'YearTerm': '2020Summer'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '513', 'Course Title': 'Theory and Practice of Data Cleaning', 'Term': 'Summer', 'Year': 2021, 'YearTerm': '2021Summer'},
{'Average_Gpa': 3.9562500000000003, 'Subject': 'CS', 'Number': '598fdc', 'Course Title': 'Foundations of Data Curation', 'Term': 'Fall', 'Year': 2020, 'YearTerm': '2020Fall'},
{'Average_Gpa': 3.9562500000000003, 'Subject': 'CS', 'Number': '598fdc', 'Course Title': 'Foundations of Data Curation', 'Term': 'Fall', 'Year': 2021, 'YearTerm': '2021Fall'},
{'Average_Gpa': 3.798305084745763, 'Subject': 'CS', 'Number': '598psl', 'Course Title': 'Practical Statistical Learning', 'Term': 'Fall', 'Year': 2020, 'YearTerm': '2020Fall'},
{'Average_Gpa': 3.798305084745763, 'Subject': 'CS', 'Number': '598psl', 'Course Title': 'Practical Statistical Learning', 'Term': 'Fall', 'Year': 2021, 'YearTerm': '2021Fall'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '598ccc', 'Course Title': 'Cloud Computing Capstone', 'Term': 'Fall', 'Year': 2020, 'YearTerm': '2020Fall'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '598ccc', 'Course Title': 'Cloud Computing Capstone', 'Term': 'Fall', 'Year': 2021, 'YearTerm': '2021Fall'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '598ccc', 'Course Title': 'Cloud Computing Capstone', 'Term': 'Summer', 'Year': 2020, 'YearTerm': '2020Summer'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '598ccc', 'Course Title': 'Cloud Computing Capstone', 'Term': 'Summer', 'Year': 2021, 'YearTerm': '2021Summer'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '598dmc', 'Course Title': 'Data Mining Capstone', 'Term': 'Summer', 'Year': 2020, 'YearTerm': '2020Summer'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '598dmc', 'Course Title': 'Data Mining Capstone', 'Term': 'Summer', 'Year': 2021, 'YearTerm': '2021Summer'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '598dmc', 'Course Title': 'Data Mining Capstone', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '598dmc', 'Course Title': 'Data Mining Capstone', 'Term': 'Spring', 'Year': 2021, 'YearTerm': '2021Spring'},
{'Average_Gpa': 3.5414814814814815, 'Subject': 'CS', 'Number': '598abm', 'Course Title': 'Advanced Bayesian Modeling', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.5414814814814815, 'Subject': 'CS', 'Number': '598abm', 'Course Title': 'Advanced Bayesian Modeling', 'Term': 'Spring', 'Year': 2021, 'YearTerm': '2021Spring'},
{'Average_Gpa': 3.2556390977443614, 'Subject': 'CS', 'Number': '418', 'Course Title': 'Interactive Computer Graphics', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '421', 'Course Title': 'Programming Languages and Compilers', 'Term': 'Summer', 'Year': 2020, 'YearTerm': '2020Summer'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '421', 'Course Title': 'Programming Languages and Compilers', 'Term': 'Summer', 'Year': 2021, 'YearTerm': '2021Summer'},
{'Average_Gpa': 3.457316148597422, 'Subject': 'CS', 'Number': '427', 'Course Title': 'Software Engineering I', 'Term': 'Fall', 'Year': 2020, 'YearTerm': '2020Fall'},
{'Average_Gpa': 3.457316148597422, 'Subject': 'CS', 'Number': '427', 'Course Title': 'Software Engineering I', 'Term': 'Fall', 'Year': 2021, 'YearTerm': '2021Fall'},
{'Average_Gpa': 3.125246753246754, 'Subject': 'CS', 'Number': '450', 'Course Title': 'Numerical Analysis', 'Term': 'Fall', 'Year': 2020, 'YearTerm': '2020Fall'},
{'Average_Gpa': 3.125246753246754, 'Subject': 'CS', 'Number': '450', 'Course Title': 'Numerical Analysis', 'Term': 'Fall', 'Year': 2021, 'YearTerm': '2021Fall'},
{'Average_Gpa': 3.125246753246754, 'Subject': 'CS', 'Number': '450', 'Course Title': 'Numerical Analysis', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.125246753246754, 'Subject': 'CS', 'Number': '450', 'Course Title': 'Numerical Analysis', 'Term': 'Spring', 'Year': 2021, 'YearTerm': '2021Spring'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '484', 'Course Title': 'Parallel Computing', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.5277, 'Subject': 'CS', 'Number': '484', 'Course Title': 'Parallel Computing', 'Term': 'Spring', 'Year': 2021, 'YearTerm': '2021Spring'},
{'Average_Gpa': 3.934090909090909, 'Subject': 'CS', 'Number': '498iot', 'Course Title': 'Internet of Things', 'Term': 'Spring', 'Year': 2020, 'YearTerm': '2020Spring'},
{'Average_Gpa': 3.934090909090909, 'Subject': 'CS', 'Number': '498iot', 'Course Title': 'Internet of Things', 'Term': 'Spring', 'Year': 2021, 'YearTerm': '2021Spring'},
{'Average_Gpa': 3.4919555437946546, 'Subject': 'STAT', 'Number': '420', 'Course Title': 'Methods of Applied Statistics', 'Term': 'Summer', 'Year': 2020, 'YearTerm': '2020Summer'},
{'Average_Gpa': 3.4919555437946546, 'Subject': 'STAT', 'Number': '420', 'Course Title': 'Methods of Applied Statistics', 'Term': 'Summer', 'Year': 2021, 'YearTerm': '2021Summer'}]
#rrr=[i for i in uiuc_mcs_courses if i.Average_Gpa !=0]
#print(sum([i.Average_Gpa for i in rrr])/(float(len(rrr))))
for i in precomputed_data:
	uiuc_mcs_courses.append(Course(**i))
path_rules  = []
path_rules.append(make_prereq_rule("cs498aml", "cs598psl"))
path_rules.append(make_prereq_rule("cs425", "cs598ccc"))
path_rules.append(make_prereq_rule("cs410", "cs598dmc"))
path_rules.append(make_prereq_rule("cs412", "cs598dmc"))
path_rules.append(make_prereq_rule("cs410", "cs598psl"))
path_rules.append(make_prereq_rule("cs412", "cs598psl"))
path_rules.append(make_prereq_rule("cs445", "cs598psl"))
path_rules.append(make_prereq_rule("stat420", "cs598psl"))
path_rules.append(make_enforce_max_courses_per_term(2))
course_requirements = []
course_requirements.append(make_hours_requiment(32))
course_requirements.append(make_rule_min_num_courses(8))
course_requirements.append(make_rule_must_do_n_of_subset(1, set(["cs498aml", "cs445"])))
course_requirements.append(make_rule_must_do_n_of_subset(1, set(["cs410","cs411","cs412"])))
course_requirements.append(make_rule_must_do_n_of_subset(1, set(["cs498dv"])))
course_requirements.append(make_rule_must_do_n_of_subset(3, set(["cs513","cs598fdc","cs598psl","cs598abm","cs598ccc","cs598dmc"])))
course_requirements.append(make_rule_must_do_n_of_subset(1, set(["cs425","cs498cca","cs498cn"])))
p = Program(uiuc_mcs_courses, course_requirements)
for i in p.get_best_path(path_rules, []):
	x=[]
	for c in  i.courses:
		x.append((c.id, c.YearTerm))
	print("Courses:" +str(x))
	print("Average GPA:" + str(sum([q.Average_Gpa for q in i.courses])/float(len(i.courses))))
	print('')	
#print(p.get_best_path(path_rules, [uiuc_mcs_courses[1]]))
