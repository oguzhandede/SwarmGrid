namespace SwarmGrid.Application.RiskEngine;

/// <summary>
/// A thread-safe bounded queue that automatically removes oldest items when capacity is reached.
/// </summary>
/// <typeparam name="T">The type of elements in the queue.</typeparam>
public class BoundedQueue<T>
{
    private readonly Queue<T> _queue = new();
    private readonly int _capacity;
    private readonly object _lock = new();
    
    public BoundedQueue(int capacity)
    {
        _capacity = capacity;
    }
    
    /// <summary>
    /// Adds an item to the queue, removing the oldest if at capacity.
    /// </summary>
    public void Enqueue(T item)
    {
        lock (_lock)
        {
            while (_queue.Count >= _capacity)
            {
                _queue.Dequeue();
            }
            _queue.Enqueue(item);
        }
    }
    
    /// <summary>
    /// Returns all current items as a list.
    /// </summary>
    public List<T> ToList()
    {
        lock (_lock)
        {
            return _queue.ToList();
        }
    }
    
    public int Count
    {
        get
        {
            lock (_lock)
            {
                return _queue.Count;
            }
        }
    }
}
