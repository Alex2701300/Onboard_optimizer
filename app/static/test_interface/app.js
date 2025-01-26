
const InputField = ({ label, type = "text", value, onChange, required = false, min, max }) => (
    <div className="form-field">
        <label>{label}</label>
        <input
            type={type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            required={required}
            min={min}
            max={max}
            className="input"
        />
    </div>
);

const SelectField = ({ label, options, value, onChange, required = false }) => (
    <div className="form-field">
        <label>{label}</label>
        <select 
            value={value} 
            onChange={(e) => onChange(e.target.value)}
            required={required}
            className="input"
        >
            {options.map(option => (
                <option key={option.value} value={option.value}>
                    {option.label}
                </option>
            ))}
        </select>
    </div>
);

const VehicleManager = () => {
    const [activeTab, setActiveTab] = React.useState('car');
    const [message, setMessage] = React.useState({ type: '', text: '' });
    const [carForm, setCarForm] = React.useState({
        vin: '',
        make: '',
        model: '',
        year: '',
        length: '',
        width: '',
        height: '',
        wheelbase: '',
        body_type: 'sedan',
        status: 'run_and_drive'
    });

    const handleCarSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('/api/vehicles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: 'car',
                    ...carForm
                }),
            });

            if (response.ok) {
                setMessage({ type: 'success', text: 'Car added successfully!' });
                setCarForm({
                    vin: '',
                    make: '',
                    model: '',
                    year: '',
                    length: '',
                    width: '',
                    height: '',
                    wheelbase: '',
                    body_type: 'sedan',
                    status: 'run_and_drive'
                });
            } else {
                setMessage({ type: 'error', text: 'Failed to add car.' });
            }
        } catch (error) {
            setMessage({ type: 'error', text: 'Error submitting form.' });
        }
    };

    return (
        <div className="container">
            <h1>CarLogix Vehicle Manager</h1>
            {message.text && (
                <div className={`message ${message.type}`}>
                    {message.text}
                </div>
            )}
            <div className="tabs">
                <button 
                    className={`tab ${activeTab === 'car' ? 'active' : ''}`}
                    onClick={() => setActiveTab('car')}
                >
                    Cars
                </button>
            </div>
            {activeTab === 'car' && (
                <form onSubmit={handleCarSubmit} className="form-section">
                    <h2>Add Car</h2>
                    <div className="form-grid">
                        <div>
                            <InputField 
                                label="VIN"
                                value={carForm.vin}
                                onChange={(value) => setCarForm({...carForm, vin: value})}
                                required
                            />
                            <InputField 
                                label="Make"
                                value={carForm.make}
                                onChange={(value) => setCarForm({...carForm, make: value})}
                                required
                            />
                            <InputField 
                                label="Model"
                                value={carForm.model}
                                onChange={(value) => setCarForm({...carForm, model: value})}
                                required
                            />
                        </div>
                    </div>
                    <button type="submit" className="button">Add Car</button>
                </form>
            )}
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<VehicleManager />);
